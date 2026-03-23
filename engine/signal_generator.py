"""Signal generation from LLM analysis vs market odds."""

import json
import logging
from datetime import datetime, timezone

from engine.config import (
    SIGNAL_EDGE_THRESHOLD,
    SIGNAL_CONFIDENCE_THRESHOLD,
    STRONG_SIGNAL_EDGE,
    STRONG_SIGNAL_CONFIDENCE,
    SIGNALS_DIR,
)

logger = logging.getLogger(__name__)


def calculate_edge(llm_probability: float, market_odds: float) -> float:
    """Calculate edge between LLM estimate and market odds."""
    return llm_probability - market_odds


def generate_signal(edge: float, confidence: float) -> str:
    """Classify signal based on edge and confidence thresholds.

    Returns one of: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    """
    if edge > STRONG_SIGNAL_EDGE and confidence > STRONG_SIGNAL_CONFIDENCE:
        return "STRONG_BUY"
    elif edge > SIGNAL_EDGE_THRESHOLD and confidence > SIGNAL_CONFIDENCE_THRESHOLD:
        return "BUY"
    elif edge < -STRONG_SIGNAL_EDGE and confidence > STRONG_SIGNAL_CONFIDENCE:
        return "STRONG_SELL"
    elif edge < -SIGNAL_EDGE_THRESHOLD and confidence > SIGNAL_CONFIDENCE_THRESHOLD:
        return "SELL"
    return "HOLD"


def calculate_kelly(edge: float, confidence: float, market_odds: float, fraction: float = 0.25, max_kelly: float = 0.05) -> float:
    """Calculate fractional Kelly criterion position size.

    Kelly = (p * b - q) / b, where:
    - p = estimated probability of winning
    - q = 1 - p
    - b = odds (payout ratio)
    fraction = Kelly fraction (0.25 = quarter Kelly for safety)
    max_kelly = maximum position size cap (5% of bankroll)
    """
    if abs(edge) < 0.01 or confidence < 0.3:
        return 0.0

    if edge > 0:
        p = min(0.95, market_odds + edge)
        b = (1 / market_odds) - 1 if market_odds > 0 else 0
    else:
        p = min(0.95, (1 - market_odds) + abs(edge))
        b = (1 / (1 - market_odds)) - 1 if market_odds < 1 else 0

    if b <= 0:
        return 0.0

    q = 1 - p
    kelly = (p * b - q) / b
    kelly = max(0, kelly * fraction * confidence)
    return round(min(kelly, max_kelly), 4)


def create_signal_entry(analysis: dict, news_count: int = 0, slug: str = "", left_token_id: str = "", right_token_id: str = "") -> dict:
    """Create a full signal entry from analysis results."""
    market_odds = analysis["market_odds"]
    llm_probability = analysis["probability"]
    confidence = analysis["confidence"]
    edge = calculate_edge(llm_probability, market_odds)
    signal = generate_signal(edge, confidence)
    score = abs(edge) * confidence
    kelly_size = calculate_kelly(edge, confidence, market_odds)

    # Build Polymarket URL
    polymarket_url = f"https://polymarket.com/event/{slug}" if slug else ""

    entry = {
        "market_id": analysis["market_id"],
        "question": analysis["question"],
        "market_odds": round(market_odds, 4),
        "llm_probability": round(llm_probability, 4),
        "edge": round(edge, 4),
        "confidence": round(confidence, 4),
        "signal": signal,
        "score": round(score, 4),
        "kelly_fraction": kelly_size,
        "left_token_id": left_token_id,
        "right_token_id": right_token_id,
        "polymarket_url": polymarket_url,
        "reasoning": analysis["reasoning"],
        "key_factors": analysis["key_factors"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "news_count": news_count,
    }

    # Add ensemble data if available
    if "ensemble" in analysis:
        entry["ensemble"] = analysis["ensemble"]
    if "raw_probability" in analysis:
        entry["raw_probability"] = round(analysis["raw_probability"], 4)

    return entry


def rank_signals(signals: list[dict]) -> list[dict]:
    """Rank signals by score (edge * confidence), highest first."""
    return sorted(signals, key=lambda s: s["score"], reverse=True)


def filter_actionable(signals: list[dict]) -> list[dict]:
    """Filter out HOLD signals, keeping only actionable ones."""
    return [s for s in signals if s["signal"] != "HOLD"]


def generate_all_signals(
    analyses: list[dict],
    news_counts: dict[str, int],
    slugs: dict[str, str] | None = None,
    token_ids: dict[str, dict] | None = None,
) -> list[dict]:
    """Generate signals for all analyzed markets.

    Args:
        analyses: List of analysis results from LLMAnalyzer.batch_analyze
        news_counts: Dict mapping market_id -> number of news articles
        slugs: Dict mapping market_id -> polymarket slug
        token_ids: Dict mapping market_id -> {left_token_id, right_token_id}

    Returns:
        Ranked list of signal entries
    """
    slugs = slugs or {}
    token_ids = token_ids or {}
    signals = []
    for analysis in analyses:
        market_id = analysis["market_id"]
        count = news_counts.get(market_id, 0)
        slug = slugs.get(market_id, "")
        tokens = token_ids.get(market_id, {})
        signal = create_signal_entry(
            analysis, news_count=count, slug=slug,
            left_token_id=tokens.get("left", ""),
            right_token_id=tokens.get("right", ""),
        )
        signals.append(signal)

    signals = rank_signals(signals)

    actionable = [s for s in signals if s["signal"] != "HOLD"]
    logger.info(
        f"Generated {len(signals)} signals: "
        f"{len(actionable)} actionable, "
        f"{len(signals) - len(actionable)} HOLD"
    )

    return signals


def export_signals(signals: list[dict], path: str | None = None) -> str:
    """Export signals to JSON file."""
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)

    if path is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filepath = SIGNALS_DIR / f"signals_{timestamp}.json"
    else:
        filepath = SIGNALS_DIR / path

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_signals": len(signals),
        "actionable_signals": len([s for s in signals if s["signal"] != "HOLD"]),
        "signals": signals,
    }

    filepath.write_text(json.dumps(data, indent=2))
    logger.info(f"Exported {len(signals)} signals to {filepath}")

    # Also save as latest
    latest = SIGNALS_DIR / "latest.json"
    latest.write_text(json.dumps(data, indent=2))

    return str(filepath)


def print_signal_summary(signals: list[dict]) -> None:
    """Print a formatted summary of signals to stdout."""
    print("\n" + "=" * 80)
    print("SIGNAL SUMMARY")
    print("=" * 80)

    for s in signals:
        if s["signal"] == "HOLD":
            continue

        color_map = {
            "STRONG_BUY": "\033[92m",   # green
            "BUY": "\033[32m",           # light green
            "SELL": "\033[31m",          # red
            "STRONG_SELL": "\033[91m",   # bright red
        }
        reset = "\033[0m"
        color = color_map.get(s["signal"], "")

        print(f"\n{color}[{s['signal']}]{reset} {s['question'][:70]}")
        print(f"  Market: {s['market_odds']:.1%} | LLM: {s['llm_probability']:.1%} | Edge: {s['edge']:+.1%} | Confidence: {s['confidence']:.0%}")
        kelly = s.get('kelly_fraction', 0)
        ensemble_info = ""
        if s.get('ensemble'):
            models = s['ensemble'].get('models_used', 0)
            spread = s['ensemble'].get('spread', 0)
            ensemble_info = f" | Ensemble: {models} models, spread={spread:.2f}"
        print(f"  Score: {s['score']:.4f} | Kelly: {kelly:.1%} | News: {s['news_count']}{ensemble_info}")
        print(f"  Reasoning: {s['reasoning'][:120]}")

    hold_count = len([s for s in signals if s["signal"] == "HOLD"])
    print(f"\n--- {len(signals) - hold_count} actionable | {hold_count} hold ---\n")
