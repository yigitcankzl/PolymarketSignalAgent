"""Automated trading via Synthesis.trade API."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from engine.synthesis_client import SynthesisClient
from engine.config import SYNTHESIS_API_KEY, DATA_DIR

logger = logging.getLogger(__name__)

TRADER_DIR = DATA_DIR / "trader"


class Trader:
    """Manages accounts, wallets, and order execution via Synthesis API."""

    def __init__(self, project_api_key: str = SYNTHESIS_API_KEY):
        self.client = SynthesisClient(api_key=project_api_key)
        self.account_id: Optional[str] = None
        self.account_api_key: Optional[str] = None
        self.wallet_id: Optional[str] = None
        self._load_state()

    def _state_path(self):
        TRADER_DIR.mkdir(parents=True, exist_ok=True)
        return TRADER_DIR / "state.json"

    def _load_state(self):
        path = self._state_path()
        if path.exists():
            try:
                state = json.loads(path.read_text())
                self.account_id = state.get("account_id")
                self.account_api_key = state.get("account_api_key")
                self.wallet_id = state.get("wallet_id")
                logger.info(f"Loaded trader state: account={self.account_id}, wallet={self.wallet_id}")
            except Exception:
                pass

    def _save_state(self):
        self._state_path().write_text(json.dumps({
            "account_id": self.account_id,
            "account_api_key": self.account_api_key,
            "wallet_id": self.wallet_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, indent=2))

    # ── Account Setup ──────────────────────────────────────────────

    def setup_account(self) -> str:
        """Create a Synthesis account if not exists."""
        if self.account_id:
            logger.info(f"Account already exists: {self.account_id}")
            return self.account_id

        try:
            data = self.client._post("/api/v1/project/account", {
                "metadata": {"agent": "polymarket-signal-agent", "type": "trading-bot"}
            })
            self.account_id = data.get("account_id", data.get("id", ""))
            logger.info(f"Created account: {self.account_id}")
            self._save_state()
            return self.account_id
        except Exception as e:
            logger.error(f"Failed to create account: {e}")
            raise

    def setup_api_key(self) -> str:
        """Create an account API key for trading."""
        if self.account_api_key:
            logger.info("Account API key already exists")
            return self.account_api_key

        if not self.account_id:
            self.setup_account()

        try:
            data = self.client._post(
                f"/api/v1/project/account/{self.account_id}/api-key"
            )
            self.account_api_key = data.get("secret_key", data.get("key", ""))
            logger.info("Created account API key")
            self._save_state()
            return self.account_api_key
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            raise

    def setup_wallet(self) -> str:
        """Create or get a Polygon wallet."""
        if self.wallet_id:
            logger.info(f"Wallet already exists: {self.wallet_id}")
            return self.wallet_id

        if not self.account_api_key:
            self.setup_api_key()

        try:
            headers = {"X-API-KEY": self.account_api_key}
            import httpx
            resp = httpx.get(
                f"{self.client.base_url}/api/v1/wallets",
                headers=headers,
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            response = data.get("response", data)

            wallets = response if isinstance(response, list) else response.get("wallets", [])
            if wallets:
                self.wallet_id = wallets[0].get("wallet_id", wallets[0].get("id", ""))
            else:
                # Create new wallet
                resp = httpx.post(
                    f"{self.client.base_url}/api/v1/wallet/pol",
                    headers=headers,
                    timeout=15.0,
                )
                resp.raise_for_status()
                data = resp.json()
                response = data.get("response", data)
                self.wallet_id = response.get("wallet_id", response.get("id", ""))

            logger.info(f"Wallet ready: {self.wallet_id}")
            self._save_state()
            return self.wallet_id
        except Exception as e:
            logger.error(f"Failed to setup wallet: {e}")
            raise

    def full_setup(self) -> dict:
        """Run complete setup: account → API key → wallet."""
        print("  Setting up Synthesis trading account...")
        account_id = self.setup_account()
        print(f"  Account: {account_id}")

        print("  Creating account API key...")
        self.setup_api_key()
        print("  API key: created")

        print("  Setting up Polygon wallet...")
        wallet_id = self.setup_wallet()
        print(f"  Wallet: {wallet_id}")

        return {
            "account_id": self.account_id,
            "wallet_id": self.wallet_id,
            "status": "ready",
        }

    # ── Balance & Positions ────────────────────────────────────────

    def get_balance(self) -> dict:
        """Get wallet USDC balance."""
        if not self.wallet_id or not self.account_api_key:
            return {"balance": 0, "currency": "USDC"}

        try:
            import httpx
            resp = httpx.get(
                f"{self.client.base_url}/api/v1/wallet/pol/{self.wallet_id}/balance",
                headers={"X-API-KEY": self.account_api_key},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", data)
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {"balance": 0, "currency": "USDC"}

    def get_positions(self) -> list[dict]:
        """Get open positions."""
        if not self.wallet_id or not self.account_api_key:
            return []

        try:
            import httpx
            resp = httpx.get(
                f"{self.client.base_url}/api/v1/wallet/pol/{self.wallet_id}/positions",
                headers={"X-API-KEY": self.account_api_key},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            response = data.get("response", data)
            return response if isinstance(response, list) else response.get("positions", [])
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    def get_pnl(self) -> dict:
        """Get wallet PnL."""
        if not self.wallet_id or not self.account_api_key:
            return {}

        try:
            import httpx
            resp = httpx.get(
                f"{self.client.base_url}/api/v1/wallet/pol/{self.wallet_id}/pnl",
                headers={"X-API-KEY": self.account_api_key},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", data)
        except Exception as e:
            logger.error(f"Failed to get PnL: {e}")
            return {}

    def get_orders(self) -> list[dict]:
        """Get order history."""
        if not self.wallet_id or not self.account_api_key:
            return []

        try:
            import httpx
            resp = httpx.get(
                f"{self.client.base_url}/api/v1/wallet/pol/{self.wallet_id}/orders",
                headers={"X-API-KEY": self.account_api_key},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            response = data.get("response", data)
            return response if isinstance(response, list) else response.get("orders", [])
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            return []

    def get_deposit_address(self) -> str:
        """Get deposit address for the wallet."""
        if not self.wallet_id or not self.account_api_key:
            return ""

        try:
            import httpx
            resp = httpx.get(
                f"{self.client.base_url}/api/v1/wallet/pol",
                headers={"X-API-KEY": self.account_api_key},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            response = data.get("response", data)
            if isinstance(response, list) and response:
                return response[0].get("address", "")
            return response.get("address", "")
        except Exception as e:
            logger.error(f"Failed to get deposit address: {e}")
            return ""

    # ── Order Execution ────────────────────────────────────────────

    def place_order(
        self,
        token_id: str,
        side: str,
        amount: float,
        order_type: str = "MARKET",
        price: Optional[float] = None,
    ) -> dict:
        """Place an order on Polymarket via Synthesis.

        Args:
            token_id: The Polymarket token ID (left_token_id or right_token_id)
            side: BUY or SELL
            amount: Amount in USDC
            order_type: MARKET, LIMIT, or STOPLOSS
            price: Required for LIMIT/STOPLOSS (0.001 to 0.999)
        """
        if not self.wallet_id or not self.account_api_key:
            raise ValueError("Wallet not set up. Run full_setup() first.")

        order_body = {
            "token_id": token_id,
            "side": side,
            "type": order_type,
            "amount": str(amount),
            "units": "USDC",
        }
        if price is not None and order_type in ("LIMIT", "STOPLOSS"):
            order_body["price"] = str(price)

        try:
            import httpx
            resp = httpx.post(
                f"{self.client.base_url}/api/v1/wallet/pol/{self.wallet_id}/order",
                headers={
                    "X-API-KEY": self.account_api_key,
                    "Content-Type": "application/json",
                },
                json=order_body,
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            result = data.get("response", data)

            logger.info(f"Order placed: {side} ${amount} on {token_id[:20]}...")
            self._log_trade(token_id, side, amount, order_type, result)
            return result
        except Exception as e:
            logger.error(f"Order failed: {e}")
            return {"error": str(e)}

    def execute_signals(
        self,
        signals: list[dict],
        max_orders: int = 3,
        max_amount_per_order: float = 2.0,
    ) -> list[dict]:
        """Execute top signals as market orders.

        Args:
            signals: Ranked signal list from signal_generator
            max_orders: Maximum number of orders to place
            max_amount_per_order: Max USDC per order
        """
        if not self.wallet_id:
            logger.warning("No wallet configured, skipping execution")
            return []

        actionable = [s for s in signals if s["signal"] != "HOLD"][:max_orders]
        results = []

        for signal in actionable:
            side = "BUY" if signal["signal"] in ("STRONG_BUY", "BUY") else "SELL"
            kelly = signal.get("kelly_fraction", 0.01)
            amount = round(min(kelly * 100, max_amount_per_order), 2)
            if amount < 0.5:
                amount = 0.5

            # Need token_id - use market's left_token_id for YES bets
            token_id = signal.get("token_id", signal.get("left_token_id", ""))
            if not token_id:
                logger.warning(f"No token_id for {signal['question'][:30]}, skipping")
                continue

            print(f"    {side} ${amount} on {signal['question'][:50]}...")
            result = self.place_order(token_id, side, amount)
            results.append({
                "signal": signal["signal"],
                "question": signal["question"],
                "side": side,
                "amount": amount,
                "result": result,
            })

        return results

    def _log_trade(self, token_id: str, side: str, amount: float, order_type: str, result: dict):
        """Log trade to file."""
        TRADER_DIR.mkdir(parents=True, exist_ok=True)
        log_path = TRADER_DIR / "trades.json"
        trades = []
        if log_path.exists():
            try:
                trades = json.loads(log_path.read_text())
            except Exception:
                pass
        trades.append({
            "token_id": token_id,
            "side": side,
            "amount": amount,
            "type": order_type,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        log_path.write_text(json.dumps(trades, indent=2, default=str))

    # ── Dashboard Data ─────────────────────────────────────────────

    def get_dashboard_data(self) -> dict:
        """Get all trading data for dashboard display."""
        return {
            "account_id": self.account_id,
            "wallet_id": self.wallet_id,
            "balance": self.get_balance(),
            "positions": self.get_positions(),
            "pnl": self.get_pnl(),
            "orders": self.get_orders(),
            "deposit_address": self.get_deposit_address(),
            "status": "active" if self.wallet_id else "not_configured",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def export_dashboard_data(self) -> str:
        """Export trading data for dashboard."""
        TRADER_DIR.mkdir(parents=True, exist_ok=True)
        data = self.get_dashboard_data()
        path = TRADER_DIR / "latest.json"
        path.write_text(json.dumps(data, indent=2, default=str))
        return str(path)

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
