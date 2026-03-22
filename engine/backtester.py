"""Backtesting engine for signal performance evaluation."""

import json
import math
import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from engine.config import BACKTEST_DIR

logger = logging.getLogger(__name__)


def calculate_trade_pnl(signal: dict, resolution: float) -> float:
    """Calculate P&L for a single trade.

    For BUY signals: pnl = (resolution - market_odds) * position_size
    For SELL signals: pnl = (market_odds - resolution) * position_size
    Position size is fixed at 1.0.
    """
    market_odds = signal["market_odds"]
    signal_type = signal["signal"]

    if signal_type in ("STRONG_BUY", "BUY"):
        return resolution - market_odds
    elif signal_type in ("STRONG_SELL", "SELL"):
        return market_odds - resolution
    return 0.0


def run_backtest(signals: list[dict], resolutions: dict[str, float]) -> dict:
    """Run backtest on a list of signals with known resolutions.

    Args:
        signals: List of signal dicts (from signal_generator)
        resolutions: Dict mapping market_id -> resolution (1.0 or 0.0)

    Returns:
        Dict with trades, metrics, and PnL curve
    """
    trades = []

    for signal in signals:
        market_id = signal["market_id"]
        if market_id not in resolutions:
            continue
        if signal["signal"] == "HOLD":
            continue

        resolution = resolutions[market_id]
        pnl = calculate_trade_pnl(signal, resolution)

        is_correct = (
            (signal["signal"] in ("STRONG_BUY", "BUY") and resolution == 1.0) or
            (signal["signal"] in ("STRONG_SELL", "SELL") and resolution == 0.0)
        )

        trades.append({
            "market_id": market_id,
            "question": signal["question"],
            "signal": signal["signal"],
            "market_odds": signal["market_odds"],
            "llm_probability": signal["llm_probability"],
            "edge": signal["edge"],
            "confidence": signal["confidence"],
            "resolution": resolution,
            "pnl": round(pnl, 4),
            "correct": is_correct,
            "timestamp": signal.get("timestamp", ""),
        })

    metrics = calculate_metrics(trades)
    pnl_curve = generate_pnl_curve(trades)

    return {
        "trades": trades,
        "metrics": metrics,
        "pnl_curve": pnl_curve,
    }


def calculate_metrics(trades: list[dict]) -> dict:
    """Calculate performance metrics from trade results."""
    if not trades:
        return _empty_metrics()

    total = len(trades)
    correct = sum(1 for t in trades if t["correct"])
    pnls = [t["pnl"] for t in trades]
    total_pnl = sum(pnls)
    winning = [p for p in pnls if p > 0]
    losing = [p for p in pnls if p < 0]

    # Hit rate
    hit_rate = correct / total if total > 0 else 0

    # Sharpe ratio (annualized, assuming daily)
    if len(pnls) > 1:
        avg_return = sum(pnls) / len(pnls)
        std_return = (sum((p - avg_return) ** 2 for p in pnls) / (len(pnls) - 1)) ** 0.5
        sharpe = (avg_return / std_return * math.sqrt(252)) if std_return > 0 else 0
    else:
        sharpe = 0

    # Max drawdown
    cumulative = []
    running = 0
    peak = 0
    max_dd = 0
    for pnl in pnls:
        running += pnl
        cumulative.append(running)
        if running > peak:
            peak = running
        dd = peak - running
        if dd > max_dd:
            max_dd = dd

    # Profit factor
    gross_profit = sum(winning) if winning else 0
    gross_loss = abs(sum(losing)) if losing else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0

    # Win rate by signal type
    signal_types = {}
    for t in trades:
        sig = t["signal"]
        if sig not in signal_types:
            signal_types[sig] = {"total": 0, "correct": 0}
        signal_types[sig]["total"] += 1
        if t["correct"]:
            signal_types[sig]["correct"] += 1

    win_rate_by_signal = {
        sig: round(data["correct"] / data["total"], 4) if data["total"] > 0 else 0
        for sig, data in signal_types.items()
    }

    return {
        "total_signals": total,
        "correct_signals": correct,
        "hit_rate": round(hit_rate, 4),
        "total_pnl": round(total_pnl, 4),
        "avg_pnl": round(total_pnl / total, 4),
        "avg_edge": round(sum(t["edge"] for t in trades) / total, 4),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": round(max_dd, 4),
        "profit_factor": round(profit_factor, 4) if profit_factor != float("inf") else 999.0,
        "win_count": len(winning),
        "loss_count": len(losing),
        "best_trade": round(max(pnls), 4) if pnls else 0,
        "worst_trade": round(min(pnls), 4) if pnls else 0,
        "win_rate_by_signal": win_rate_by_signal,
    }


def _empty_metrics() -> dict:
    return {
        "total_signals": 0,
        "correct_signals": 0,
        "hit_rate": 0,
        "total_pnl": 0,
        "avg_pnl": 0,
        "avg_edge": 0,
        "sharpe_ratio": 0,
        "max_drawdown": 0,
        "profit_factor": 0,
        "win_count": 0,
        "loss_count": 0,
        "best_trade": 0,
        "worst_trade": 0,
        "win_rate_by_signal": {},
    }


def generate_pnl_curve(trades: list[dict]) -> list[dict]:
    """Generate cumulative PnL curve data points."""
    curve = []
    cumulative = 0

    for i, trade in enumerate(trades):
        cumulative += trade["pnl"]
        curve.append({
            "trade_number": i + 1,
            "market_id": trade["market_id"],
            "question": trade["question"][:50],
            "signal": trade["signal"],
            "pnl": trade["pnl"],
            "cumulative_pnl": round(cumulative, 4),
            "timestamp": trade.get("timestamp", ""),
        })

    return curve


def export_results(
    metrics: dict,
    pnl_curve: list[dict],
    trades: list[dict],
    path: Optional[str] = None,
) -> str:
    """Export backtest results to JSON."""
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

    if path is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filepath = BACKTEST_DIR / f"backtest_{timestamp}.json"
    else:
        filepath = BACKTEST_DIR / path

    data = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "pnl_curve": pnl_curve,
        "trades": trades,
    }

    filepath.write_text(json.dumps(data, indent=2))

    # Also save as latest
    latest = BACKTEST_DIR / "latest.json"
    latest.write_text(json.dumps(data, indent=2))

    logger.info(f"Exported backtest results to {filepath}")
    return str(filepath)


def print_backtest_summary(metrics: dict) -> None:
    """Print formatted backtest metrics to stdout."""
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    print(f"  Total Trades:   {metrics['total_signals']}")
    print(f"  Hit Rate:       {metrics['hit_rate']:.1%}")
    print(f"  Total P&L:      {metrics['total_pnl']:+.4f}")
    print(f"  Avg P&L:        {metrics['avg_pnl']:+.4f}")
    print(f"  Sharpe Ratio:   {metrics['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown:   {metrics['max_drawdown']:.4f}")
    print(f"  Profit Factor:  {metrics['profit_factor']:.2f}")
    print(f"  Best Trade:     {metrics['best_trade']:+.4f}")
    print(f"  Worst Trade:    {metrics['worst_trade']:+.4f}")
    print(f"  Wins/Losses:    {metrics['win_count']}/{metrics['loss_count']}")

    if metrics["win_rate_by_signal"]:
        print("\n  Win Rate by Signal:")
        for sig, rate in metrics["win_rate_by_signal"].items():
            print(f"    {sig:15s} {rate:.1%}")

    print("=" * 60 + "\n")
