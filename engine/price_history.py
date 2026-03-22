"""Fetch historical price data from Polymarket CLOB API."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from engine.config import DATA_DIR

logger = logging.getLogger(__name__)

CLOB_BASE_URL = "https://clob.polymarket.com"
HISTORY_DIR = DATA_DIR / "price_history"


def fetch_price_history(
    token_id: str,
    interval: str = "1d",
    fidelity: int = 60,
) -> list[dict]:
    """Fetch price history for a token from Polymarket CLOB API.

    Args:
        token_id: The condition token ID
        interval: Time interval (1h, 6h, 1d, 1w, 1m, all)
        fidelity: Data point frequency in minutes

    Returns:
        List of {timestamp, price} data points
    """
    try:
        resp = httpx.get(
            f"{CLOB_BASE_URL}/prices-history",
            params={"market": token_id, "interval": interval, "fidelity": fidelity},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

        history = []
        for point in data.get("history", []):
            history.append({
                "timestamp": point.get("t", 0),
                "price": float(point.get("p", 0)),
            })

        logger.info(f"Fetched {len(history)} price points for token {token_id[:12]}...")
        return history
    except Exception as e:
        logger.warning(f"Failed to fetch price history for {token_id[:12]}...: {e}")
        return []


def save_price_history(market_id: str, history: list[dict]) -> None:
    """Save price history for a market."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    filepath = HISTORY_DIR / f"{market_id}.json"
    filepath.write_text(json.dumps(history, indent=2))


def load_price_history(market_id: str) -> Optional[list[dict]]:
    """Load cached price history."""
    filepath = HISTORY_DIR / f"{market_id}.json"
    if not filepath.exists():
        return None
    try:
        return json.loads(filepath.read_text())
    except json.JSONDecodeError:
        return None
