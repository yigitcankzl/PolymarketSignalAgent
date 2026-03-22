"""Arbitrage detection for prediction markets."""

import json
import logging
from datetime import datetime, timezone

from engine.config import DATA_DIR

logger = logging.getLogger(__name__)

ARBITRAGE_DIR = DATA_DIR / "arbitrage"


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


def scan_all_arbitrage(markets: list[dict]) -> dict:
    """Run all arbitrage detection scans."""
    intra = detect_intra_market_arb(markets)
    related = detect_related_market_arb(markets)

    result = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "markets_scanned": len(markets),
        "intra_market": intra,
        "related_market": related,
        "total_opportunities": len(intra) + len(related),
    }

    # Save to file
    ARBITRAGE_DIR.mkdir(parents=True, exist_ok=True)
    filepath = ARBITRAGE_DIR / "latest.json"
    filepath.write_text(json.dumps(result, indent=2))

    return result
