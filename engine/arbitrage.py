"""Arbitrage detection for prediction markets (intra-market + cross-platform)."""

import json
import logging
import re
from datetime import datetime, timezone

from engine.config import DATA_DIR

logger = logging.getLogger(__name__)

ARBITRAGE_DIR = DATA_DIR / "arbitrage"

SYNTHESIS_BASE_URL = "https://synthesis.trade/market"


def detect_intra_market_arb(markets: list[dict], threshold: float = 0.02) -> list[dict]:
    """Detect arbitrage when YES + NO prices sum to less than 1.0.

    If YES bid + NO bid < 1.0, buying both guarantees profit.
    threshold: minimum profit margin to flag (default 2%).
    """
    opportunities = []

    for market in markets:
        yes_odds = market.get("yes_odds", 0.5)
        no_odds = market.get("no_odds", 0.5)
        total = yes_odds + no_odds

        if total < (1.0 - threshold):
            profit_pct = (1.0 - total) * 100
            opportunities.append({
                "type": "intra_market",
                "market_id": market["id"],
                "question": market["question"],
                "yes_price": round(yes_odds, 4),
                "no_price": round(no_odds, 4),
                "total_cost": round(total, 4),
                "guaranteed_profit_pct": round(profit_pct, 2),
                "slug": market.get("slug", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    opportunities.sort(key=lambda x: x["guaranteed_profit_pct"], reverse=True)
    logger.info(f"Found {len(opportunities)} intra-market arbitrage opportunities")
    return opportunities


def detect_related_market_arb(markets: list[dict], threshold: float = 0.05) -> list[dict]:
    """Detect pricing inconsistencies between related markets.

    Looks for markets with similar questions but different odds,
    which may indicate mispricing.
    """
    opportunities = []
    seen = set()

    for i, m1 in enumerate(markets):
        for m2 in markets[i + 1:]:
            pair_key = f"{m1['id']}_{m2['id']}"
            if pair_key in seen:
                continue
            seen.add(pair_key)

            # Simple keyword overlap check
            words1 = set(m1["question"].lower().split())
            words2 = set(m2["question"].lower().split())
            overlap = len(words1 & words2) / max(len(words1 | words2), 1)

            if overlap > 0.5:  # >50% word overlap = related
                odds_diff = abs(m1["yes_odds"] - m2["yes_odds"])
                if odds_diff > threshold:
                    opportunities.append({
                        "type": "related_market",
                        "market_1": {
                            "id": m1["id"],
                            "question": m1["question"],
                            "odds": round(m1["yes_odds"], 4),
                        },
                        "market_2": {
                            "id": m2["id"],
                            "question": m2["question"],
                            "odds": round(m2["yes_odds"], 4),
                        },
                        "odds_difference": round(odds_diff, 4),
                        "overlap_score": round(overlap, 3),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

    opportunities.sort(key=lambda x: x["odds_difference"], reverse=True)
    logger.info(f"Found {len(opportunities)} related-market pricing discrepancies")
    return opportunities


def _normalize_question(q: str) -> str:
    """Normalize a question for fuzzy matching."""
    q = q.lower()
    q = re.sub(r"[^\w\s]", "", q)
    stop = {"will", "the", "be", "a", "an", "in", "by", "of", "to", "for", "at", "on", "is", "it"}
    return " ".join(w for w in q.split() if w not in stop)


def _question_similarity(q1: str, q2: str) -> float:
    """Calculate word-overlap similarity between two questions."""
    w1 = set(_normalize_question(q1).split())
    w2 = set(_normalize_question(q2).split())
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / max(len(w1 | w2), 1)


def detect_cross_platform_arb(
    polymarket_markets: list[dict],
    kalshi_markets: list[dict],
    similarity_threshold: float = 0.4,
    price_threshold: float = 0.03,
) -> list[dict]:
    """Detect price discrepancies between Polymarket and Kalshi for similar markets.

    This is the core value proposition: same event priced differently on
    two platforms → trade via Synthesis.trade to capture the spread.
    """
    opportunities = []

    for pm in polymarket_markets:
        for km in kalshi_markets:
            similarity = _question_similarity(pm["question"], km["question"])
            if similarity < similarity_threshold:
                continue

            pm_price = pm.get("yes_odds", 0.5)
            km_price = km.get("yes_price", 0.5)
            price_diff = abs(pm_price - km_price)

            if price_diff < price_threshold:
                continue

            # Determine direction: buy cheap, sell expensive
            if pm_price < km_price:
                action = "BUY on Polymarket, SELL on Kalshi"
                buy_platform = "polymarket"
                sell_platform = "kalshi"
                buy_price = pm_price
                sell_price = km_price
            else:
                action = "BUY on Kalshi, SELL on Polymarket"
                buy_platform = "kalshi"
                sell_platform = "polymarket"
                buy_price = km_price
                sell_price = pm_price

            slug = pm.get("slug", "")
            synthesis_url = f"{SYNTHESIS_BASE_URL}/{slug}" if slug else ""

            opportunities.append({
                "type": "cross_platform",
                "polymarket": {
                    "id": pm.get("id", ""),
                    "question": pm["question"],
                    "yes_price": round(pm_price, 4),
                    "slug": slug,
                },
                "kalshi": {
                    "id": km.get("id", ""),
                    "question": km["question"],
                    "yes_price": round(km_price, 4),
                    "event_ticker": km.get("event_ticker", ""),
                },
                "price_difference": round(price_diff, 4),
                "profit_potential_pct": round(price_diff * 100, 2),
                "similarity_score": round(similarity, 3),
                "action": action,
                "buy_platform": buy_platform,
                "sell_platform": sell_platform,
                "buy_price": round(buy_price, 4),
                "sell_price": round(sell_price, 4),
                "synthesis_url": synthesis_url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    opportunities.sort(key=lambda x: x["price_difference"], reverse=True)
    logger.info(f"Found {len(opportunities)} cross-platform arbitrage opportunities")
    return opportunities


def scan_all_arbitrage(
    polymarket_markets: list[dict],
    kalshi_markets: list[dict] | None = None,
) -> dict:
    """Run all arbitrage detection scans."""
    intra = detect_intra_market_arb(polymarket_markets)
    related = detect_related_market_arb(polymarket_markets)

    cross_platform = []
    if kalshi_markets:
        cross_platform = detect_cross_platform_arb(polymarket_markets, kalshi_markets)

    result = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "markets_scanned": len(polymarket_markets),
        "kalshi_markets_scanned": len(kalshi_markets) if kalshi_markets else 0,
        "intra_market": intra,
        "related_market": related,
        "cross_platform": cross_platform,
        "total_opportunities": len(intra) + len(related) + len(cross_platform),
    }

    # Save to file
    ARBITRAGE_DIR.mkdir(parents=True, exist_ok=True)
    filepath = ARBITRAGE_DIR / "latest.json"
    filepath.write_text(json.dumps(result, indent=2))

    return result
