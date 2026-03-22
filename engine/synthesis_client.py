"""Synthesis.trade unified API client for Polymarket + Kalshi."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from engine.config import SYNTHESIS_API_KEY, SYNTHESIS_BASE_URL, DATA_DIR

logger = logging.getLogger(__name__)

SYNTHESIS_MARKETS_DIR = DATA_DIR / "synthesis"


class SynthesisClient:
    """Unified client for Synthesis.trade API.

    Provides access to both Polymarket and Kalshi markets through
    a single API, with cross-platform features like similar market
    pairs and unified news.
    """

    def __init__(
        self,
        api_key: str = SYNTHESIS_API_KEY,
        base_url: str = SYNTHESIS_BASE_URL,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.Client(
            timeout=20.0,
            headers=self._auth_headers(),
        )

    def _auth_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-PROJECT-API-KEY"] = self.api_key
        return headers

    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"GET {url}")
        resp = self.client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return data.get("response", data)
        return data

    def _post(self, endpoint: str, body: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"POST {url}")
        resp = self.client.post(url, json=body or {})
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return data.get("response", data)
        return data

    # ── Markets (unified) ──────────────────────────────────────────

    def search_markets(self, query: str, venue: str = "") -> list[dict]:
        """Search markets across Polymarket and Kalshi.

        Args:
            query: Search term
            venue: Filter by venue ('polymarket', 'kalshi', or '' for both)
        """
        try:
            endpoint = f"/api/v1/markets/search/{query}"
            params = {}
            if venue:
                params["venue"] = venue
            data = self._get(endpoint, params=params)
            markets = data if isinstance(data, list) else data.get("data", data.get("markets", []))
            logger.info(f"Search '{query}': found {len(markets)} markets")
            return markets
        except Exception as e:
            logger.error(f"Market search failed: {e}")
            return []

    def get_markets(self, limit: int = 50) -> list[dict]:
        """Get active markets from both platforms."""
        try:
            data = self._get("/api/v1/markets", params={"limit": limit})
            markets = data if isinstance(data, list) else data.get("data", data.get("markets", []))
            logger.info(f"Fetched {len(markets)} unified markets")
            return markets
        except Exception as e:
            logger.error(f"Get markets failed: {e}")
            return []

    def get_market_prices(self, market_ids: list[str]) -> dict:
        """Get current prices for multiple markets."""
        try:
            data = self._post("/api/v1/markets/prices", {"market_ids": market_ids})
            return data
        except Exception as e:
            logger.error(f"Get prices failed: {e}")
            return {}

    def get_market_sparklines(self, market_ids: list[str]) -> dict:
        """Get sparkline data for multiple markets."""
        try:
            data = self._post("/api/v1/markets/sparklines", {"market_ids": market_ids})
            return data
        except Exception as e:
            logger.error(f"Get sparklines failed: {e}")
            return {}

    def get_orderbooks(self, market_ids: list[str]) -> dict:
        """Get orderbook data for multiple markets."""
        try:
            data = self._post("/api/v1/markets/orderbooks", {"market_ids": market_ids})
            return data
        except Exception as e:
            logger.error(f"Get orderbooks failed: {e}")
            return {}

    def get_similar_pairs(self) -> list[dict]:
        """Get similar market pairs across platforms.

        Returns pairs of similar markets on different venues,
        perfect for cross-platform arbitrage detection.
        """
        try:
            data = self._get("/api/v1/markets/similar/pairs")
            pairs = data if isinstance(data, list) else data.get("data", data.get("pairs", []))
            logger.info(f"Found {len(pairs)} similar cross-platform pairs")
            return pairs
        except Exception as e:
            logger.error(f"Get similar pairs failed: {e}")
            return []

    def get_related_markets(self, market_id: str) -> list[dict]:
        """Get markets related to a specific market."""
        try:
            data = self._get(f"/api/v1/markets/related", params={"market_id": market_id})
            return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            logger.error(f"Get related markets failed: {e}")
            return []

    def get_venue_statistics(self) -> dict:
        """Get statistics across venues (volume, markets, etc.)."""
        try:
            return self._get("/api/v1/markets/venues/statistics")
        except Exception as e:
            logger.error(f"Get venue stats failed: {e}")
            return {}

    # ── Polymarket specific ────────────────────────────────────────

    def get_polymarket_markets(self, limit: int = 50) -> list[dict]:
        """Get active Polymarket markets."""
        try:
            data = self._get("/api/v1/polymarket/markets", params={"limit": limit})
            markets = data if isinstance(data, list) else data.get("data", data.get("markets", []))
            logger.info(f"Fetched {len(markets)} Polymarket markets via Synthesis")
            return markets
        except Exception as e:
            logger.error(f"Get Polymarket markets failed: {e}")
            return []

    def get_polymarket_market_by_slug(self, slug: str) -> Optional[dict]:
        """Get a specific Polymarket market by slug."""
        try:
            return self._get(f"/api/v1/polymarket/market/{slug}")
        except Exception as e:
            logger.error(f"Get Polymarket market {slug} failed: {e}")
            return None

    def get_polymarket_price_history(self, market_id: str) -> list[dict]:
        """Get price history for a Polymarket market."""
        try:
            data = self._get(f"/api/v1/polymarket/market/{market_id}/history")
            return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            logger.error(f"Get price history failed: {e}")
            return []

    def get_polymarket_statistics(self, market_id: str) -> dict:
        """Get statistics for a Polymarket market."""
        try:
            return self._get(f"/api/v1/polymarket/market/{market_id}/statistics")
        except Exception as e:
            logger.error(f"Get statistics failed: {e}")
            return {}

    # ── Kalshi specific ────────────────────────────────────────────

    def get_kalshi_markets(self, limit: int = 50) -> list[dict]:
        """Get active Kalshi markets."""
        try:
            data = self._get("/api/v1/kalshi/markets", params={"limit": limit})
            markets = data if isinstance(data, list) else data.get("data", data.get("markets", []))
            logger.info(f"Fetched {len(markets)} Kalshi markets via Synthesis")
            return markets
        except Exception as e:
            logger.error(f"Get Kalshi markets failed: {e}")
            return []

    def get_kalshi_price_history(self, market_id: str) -> list[dict]:
        """Get price history for a Kalshi market."""
        try:
            data = self._get(f"/api/v1/kalshi/market/{market_id}/history")
            return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            logger.error(f"Get Kalshi price history failed: {e}")
            return []

    def get_kalshi_candlesticks(self, market_id: str) -> list[dict]:
        """Get candlestick data for a Kalshi market."""
        try:
            data = self._get(f"/api/v1/kalshi/market/{market_id}/candlesticks")
            return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            logger.error(f"Get candlesticks failed: {e}")
            return []

    # ── News ───────────────────────────────────────────────────────

    def get_news(self, limit: int = 20) -> list[dict]:
        """Get latest prediction market news."""
        try:
            data = self._get("/api/v1/news", params={"limit": limit})
            return data if isinstance(data, list) else data.get("data", data.get("articles", []))
        except Exception as e:
            logger.error(f"Get news failed: {e}")
            return []

    def get_market_news(self, market_id: str) -> list[dict]:
        """Get news specific to a market."""
        try:
            data = self._get(f"/api/v1/news/market/{market_id}")
            return data if isinstance(data, list) else data.get("data", data.get("articles", []))
        except Exception as e:
            logger.error(f"Get market news failed: {e}")
            return []

    # ── Cross-platform arbitrage ───────────────────────────────────

    @staticmethod
    def _event_similarity(e1: str, e2: str) -> float:
        """Check if two event titles refer to the same competition."""
        e1, e2 = e1.lower().strip(), e2.lower().strip()
        # Normalize common variations
        for old, new in [
            ("2025-26", "2026"), ("2025–26", "2026"), ("25-26", "2026"),
            ("uefa ", ""), ("fifa ", ""), (" - winner", ""),
            ("?", ""), ("winner", ""), ("champion", ""),
            ("pro hockey", "nhl stanley cup"), ("pro baseball", "mlb"),
            ("men's ", ""), ("2026 ", ""), ("the ", ""),
        ]:
            e1 = e1.replace(old, new)
            e2 = e2.replace(old, new)

        w1 = set(e1.split())
        w2 = set(e2.split())
        if not w1 or not w2:
            return 0.0
        return len(w1 & w2) / max(len(w1 | w2), 1)

    def detect_arbitrage(self, min_price_diff: float = 0.02) -> list[dict]:
        """Detect cross-platform arbitrage by matching outcomes across platforms.

        Fetches all markets from Polymarket and Kalshi, matches by outcome
        name, then verifies the event is the same before flagging price differences.
        """
        # Build flat outcome maps from both platforms
        pm_outcomes: dict[str, dict] = {}
        for entry in self.get_polymarket_markets(limit=50):
            event = entry.get("event", {})
            for m in entry.get("markets", []):
                outcome = (m.get("outcome") or "").strip().lower()
                price = float(m.get("left_price", 0))
                if outcome and price > 0:
                    pm_outcomes[outcome] = {
                        "price": price,
                        "question": m.get("question", ""),
                        "outcome_raw": m.get("outcome", ""),
                        "event_title": event.get("title", ""),
                        "slug": event.get("slug", ""),
                        "id": m.get("condition_id", ""),
                    }

        km_outcomes: dict[str, dict] = {}
        for entry in self.get_kalshi_markets(limit=50):
            event = entry.get("event", {})
            for m in entry.get("markets", []):
                outcome = (m.get("outcome") or "").strip().lower()
                price = float(m.get("left_price", 0))
                if outcome and price > 0:
                    km_outcomes[outcome] = {
                        "price": price,
                        "question": m.get("title", ""),
                        "outcome_raw": m.get("outcome", ""),
                        "event_title": event.get("title", ""),
                        "id": m.get("market_id", ""),
                    }

        logger.info(f"Arbitrage scan: {len(pm_outcomes)} PM outcomes, {len(km_outcomes)} KA outcomes")

        # Find matching outcomes with same event
        matches = set(pm_outcomes.keys()) & set(km_outcomes.keys())
        opportunities = []

        for outcome in matches:
            pm = pm_outcomes[outcome]
            km = km_outcomes[outcome]

            # Verify events are the same (not just same team in different competitions)
            event_sim = self._event_similarity(pm["event_title"], km["event_title"])
            if event_sim < 0.25:
                continue

            diff = abs(pm["price"] - km["price"])
            if diff < min_price_diff:
                continue

            if pm["price"] < km["price"]:
                action = "BUY on Polymarket, SELL on Kalshi"
                buy_price, sell_price = pm["price"], km["price"]
            else:
                action = "BUY on Kalshi, SELL on Polymarket"
                buy_price, sell_price = km["price"], pm["price"]

            slug = pm.get("slug", "")
            opportunities.append({
                "type": "cross_platform",
                "polymarket": {
                    "id": pm["id"],
                    "question": pm["question"],
                    "outcome": pm["outcome_raw"],
                    "event": pm["event_title"],
                    "yes_price": round(pm["price"], 4),
                    "slug": slug,
                },
                "kalshi": {
                    "id": km["id"],
                    "question": km["question"],
                    "outcome": km["outcome_raw"],
                    "event": km["event_title"],
                    "yes_price": round(km["price"], 4),
                },
                "price_difference": round(diff, 4),
                "profit_potential_pct": round(diff * 100, 2),
                "event_similarity": round(event_sim, 3),
                "action": action,
                "buy_price": round(buy_price, 4),
                "sell_price": round(sell_price, 4),
                "synthesis_url": f"https://synthesis.trade/market/{slug}" if slug else "",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        opportunities.sort(key=lambda x: x["price_difference"], reverse=True)
        logger.info(f"Synthesis arbitrage: {len(opportunities)} verified opportunities")

        # Save results
        SYNTHESIS_MARKETS_DIR.mkdir(parents=True, exist_ok=True)
        arb_data = {
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "polymarket_outcomes": len(pm_outcomes),
            "kalshi_outcomes": len(km_outcomes),
            "matched_outcomes": len(matches),
            "opportunities": opportunities,
            "total": len(opportunities),
        }
        (SYNTHESIS_MARKETS_DIR / "arbitrage.json").write_text(json.dumps(arb_data, indent=2))

        # Also save to main arbitrage dir for dashboard
        arb_dir = DATA_DIR / "arbitrage"
        arb_dir.mkdir(parents=True, exist_ok=True)
        existing = {}
        arb_latest = arb_dir / "latest.json"
        if arb_latest.exists():
            try:
                existing = json.loads(arb_latest.read_text())
            except Exception:
                pass
        existing["cross_platform"] = opportunities
        existing["total_opportunities"] = existing.get("total_opportunities", 0) + len(opportunities)
        arb_latest.write_text(json.dumps(existing, indent=2))

        return opportunities

    # ── Snapshot / persistence ─────────────────────────────────────

    def save_snapshot(self, markets: list[dict]) -> str:
        """Save market snapshot."""
        SYNTHESIS_MARKETS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filepath = SYNTHESIS_MARKETS_DIR / f"snapshot_{ts}.json"
        snapshot = {"timestamp": ts, "count": len(markets), "markets": markets}
        filepath.write_text(json.dumps(snapshot, indent=2, default=str))
        latest = SYNTHESIS_MARKETS_DIR / "latest.json"
        latest.write_text(json.dumps(snapshot, indent=2, default=str))
        return str(filepath)

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
