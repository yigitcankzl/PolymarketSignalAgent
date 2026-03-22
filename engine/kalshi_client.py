"""Kalshi API client for cross-platform price comparison."""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

KALSHI_API_URL = "https://api.elections.kalshi.com/trade-api/v2"


class KalshiClient:
    """Client for Kalshi public market data."""

    def __init__(self, base_url: str = KALSHI_API_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=15.0)

    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"GET {url} params={params}")
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_events(self, limit: int = 50, status: str = "open") -> list[dict]:
        """Fetch open events from Kalshi."""
        try:
            data = self._get("/events", params={"limit": limit, "status": status})
            events = data.get("events", [])
            logger.info(f"Fetched {len(events)} Kalshi events")
            return events
        except Exception as e:
            logger.error(f"Failed to fetch Kalshi events: {e}")
            return []

    def get_markets_for_event(self, event_ticker: str) -> list[dict]:
        """Fetch markets for a specific event."""
        try:
            data = self._get(f"/events/{event_ticker}")
            event = data.get("event", {})
            markets = event.get("markets", [])
            return [self._parse_market(m) for m in markets if m]
        except Exception as e:
            logger.error(f"Failed to fetch Kalshi event {event_ticker}: {e}")
            return []

    def get_markets(self, limit: int = 100, status: str = "open") -> list[dict]:
        """Fetch open markets from Kalshi."""
        try:
            data = self._get("/markets", params={"limit": limit, "status": status})
            markets = data.get("markets", [])
            parsed = [self._parse_market(m) for m in markets if m]
            logger.info(f"Fetched {len(parsed)} Kalshi markets")
            return parsed
        except Exception as e:
            logger.error(f"Failed to fetch Kalshi markets: {e}")
            return []

    def _parse_market(self, raw: dict) -> dict:
        """Parse Kalshi market into normalized format."""
        yes_price = raw.get("yes_bid", 0) or 0
        no_price = raw.get("no_bid", 0) or 0

        # Kalshi prices are in cents (0-100), normalize to 0-1
        if yes_price > 1:
            yes_price = yes_price / 100
        if no_price > 1:
            no_price = no_price / 100

        return {
            "id": raw.get("ticker", ""),
            "event_ticker": raw.get("event_ticker", ""),
            "question": raw.get("title", ""),
            "subtitle": raw.get("subtitle", ""),
            "yes_price": round(yes_price, 4),
            "no_price": round(no_price, 4),
            "volume": raw.get("volume", 0),
            "open_interest": raw.get("open_interest", 0),
            "status": raw.get("status", ""),
            "platform": "kalshi",
        }

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
