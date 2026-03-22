"""Polymarket CLOB API client for fetching market data."""

import json
import time
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from engine.config import POLYMARKET_API_URL, MIN_VOLUME, MARKETS_DIR

logger = logging.getLogger(__name__)


class PolymarketClient:
    """Client for interacting with the Polymarket gamma API."""

    def __init__(self, base_url: str = POLYMARKET_API_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict | list:
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"GET {url} params={params}")
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_active_markets(
        self,
        limit: int = 50,
        min_volume: float = MIN_VOLUME,
        tag: Optional[str] = None,
    ) -> list[dict]:
        """Fetch active markets with sufficient volume."""
        params = {
            "limit": limit,
            "active": "true",
            "closed": "false",
            "order": "volume",
            "ascending": "false",
        }
        if tag:
            params["tag"] = tag

        raw_markets = self._get("/markets", params=params)

        markets = []
        for m in raw_markets:
            volume = float(m.get("volume", 0) or 0)
            if volume < min_volume:
                continue

            market = self._parse_market(m)
            if market:
                markets.append(market)

        logger.info(f"Fetched {len(markets)} active markets (min volume: {min_volume})")
        return markets

    def get_market_detail(self, market_id: str) -> Optional[dict]:
        """Fetch details for a single market."""
        try:
            raw = self._get(f"/markets/{market_id}")
            return self._parse_market(raw)
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch market {market_id}: {e}")
            return None

    def get_market_odds(self, market: dict) -> float:
        """Extract 'Yes' outcome probability from a market dict."""
        return market.get("yes_odds", 0.5)

    def _parse_market(self, raw: dict) -> Optional[dict]:
        """Parse raw API response into a clean market dict."""
        try:
            outcome_prices = raw.get("outcomePrices", "[]")
            if isinstance(outcome_prices, str):
                prices = json.loads(outcome_prices)
            else:
                prices = outcome_prices

            yes_odds = float(prices[0]) if prices else 0.5

            outcomes = raw.get("outcomes", "[]")
            if isinstance(outcomes, str):
                outcomes = json.loads(outcomes)

            return {
                "id": raw.get("id", ""),
                "question": raw.get("question", ""),
                "description": raw.get("description", ""),
                "slug": raw.get("slug", ""),
                "yes_odds": yes_odds,
                "no_odds": float(prices[1]) if len(prices) > 1 else 1 - yes_odds,
                "outcomes": outcomes,
                "volume": float(raw.get("volume", 0) or 0),
                "liquidity": float(raw.get("liquidity", 0) or 0),
                "end_date": raw.get("endDate", ""),
                "created_at": raw.get("createdAt", ""),
                "active": raw.get("active", True),
                "closed": raw.get("closed", False),
                "resolved": raw.get("resolved", False),
                "resolution": raw.get("resolution", None),
            }
        except (json.JSONDecodeError, IndexError, ValueError) as e:
            logger.warning(f"Failed to parse market: {e}")
            return None

    def save_snapshot(self, markets: list[dict]) -> str:
        """Save market snapshot to data/markets/ with timestamp."""
        MARKETS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filepath = MARKETS_DIR / f"snapshot_{timestamp}.json"

        snapshot = {
            "timestamp": timestamp,
            "count": len(markets),
            "markets": markets,
        }

        filepath.write_text(json.dumps(snapshot, indent=2, default=str))
        logger.info(f"Saved market snapshot: {filepath}")

        # Also save as latest
        latest = MARKETS_DIR / "latest.json"
        latest.write_text(json.dumps(snapshot, indent=2, default=str))

        return str(filepath)

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
