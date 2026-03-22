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

    def detect_arbitrage(
        self,
        polymarket_markets: list[dict],
        min_price_diff: float = 0.03,
        max_search: int = 15,
    ) -> list[dict]:
        """Detect cross-platform arbitrage by searching for matching markets.

        For each Polymarket market, searches Kalshi for the same event
        via Synthesis search API and compares prices.
        """
        opportunities = []
        searched = 0

        for pm in polymarket_markets:
            if searched >= max_search:
                break

            pm_question = pm.get("question", pm.get("title", ""))
            pm_outcome = pm.get("outcome", "")
            if not pm_question:
                continue

            # Build search query from key terms
            search_terms = pm_outcome if pm_outcome else pm_question
            # Shorten to key words for better search
            words = search_terms.split()[:5]
            query = " ".join(words)

            if len(query) < 3:
                continue

            searched += 1
            logger.info(f"  Arb search {searched}/{max_search}: '{query}'")

            try:
                kalshi_results = self.search_markets(query, venue="kalshi")
            except Exception as e:
                logger.warning(f"  Search failed: {e}")
                continue

            if not kalshi_results:
                continue

            pm_price = float(pm.get("yes_odds", pm.get("left_price", 0.5)))

            # Check each Kalshi result for price discrepancy
            for km_entry in kalshi_results[:3]:
                km_markets = km_entry.get("markets", [km_entry])
                if isinstance(km_markets, dict):
                    km_markets = [km_markets]

                for km in (km_markets if isinstance(km_markets, list) else [km_markets]):
                    km_title = km.get("title", km.get("question", ""))
                    km_price = float(km.get("left_price", km.get("yes_price", 0)))

                    if km_price <= 0 or km_price >= 1:
                        continue

                    diff = abs(pm_price - km_price)
                    if diff < min_price_diff:
                        continue

                    if pm_price < km_price:
                        action = "BUY on Polymarket, SELL on Kalshi"
                        buy_price, sell_price = pm_price, km_price
                    else:
                        action = "BUY on Kalshi, SELL on Polymarket"
                        buy_price, sell_price = km_price, pm_price

                    slug = pm.get("event_slug", pm.get("slug", ""))
                    opportunities.append({
                        "type": "cross_platform",
                        "polymarket": {
                            "id": pm.get("id", ""),
                            "question": pm_question,
                            "outcome": pm_outcome,
                            "yes_price": round(pm_price, 4),
                            "slug": slug,
                        },
                        "kalshi": {
                            "id": km.get("market_id", km.get("id", "")),
                            "question": km_title,
                            "yes_price": round(km_price, 4),
                        },
                        "price_difference": round(diff, 4),
                        "profit_potential_pct": round(diff * 100, 2),
                        "action": action,
                        "buy_price": round(buy_price, 4),
                        "sell_price": round(sell_price, 4),
                        "synthesis_url": f"https://synthesis.trade/market/{slug}" if slug else "",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    break  # One match per Kalshi result is enough

        opportunities.sort(key=lambda x: x["price_difference"], reverse=True)
        logger.info(f"Synthesis arbitrage: {len(opportunities)} opportunities found")

        # Save results
        SYNTHESIS_MARKETS_DIR.mkdir(parents=True, exist_ok=True)
        arb_path = SYNTHESIS_MARKETS_DIR / "arbitrage.json"
        arb_path.write_text(json.dumps({
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "opportunities": opportunities,
            "total": len(opportunities),
        }, indent=2))

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
