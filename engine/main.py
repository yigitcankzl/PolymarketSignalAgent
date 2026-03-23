"""CLI entry point - runs the full signal pipeline."""

import argparse
import logging
import sys
import time
from datetime import datetime, timezone

from engine.config import MAX_MARKETS, GROQ_API_KEY, SYNTHESIS_API_KEY
from engine.polymarket_client import PolymarketClient
from engine.synthesis_client import SynthesisClient
from engine.news_fetcher import fetch_news_for_market
from engine.llm_analyzer import LLMAnalyzer
from engine.signal_generator import generate_all_signals, export_signals, print_signal_summary
from engine.backtester import run_backtest, export_results, print_backtest_summary
from engine.arbitrage import scan_all_arbitrage
from engine.data_store import load_latest_signals, get_resolved_markets, load_latest_markets
from engine.config import DATA_DIR

import json as _json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _fetch_markets_synthesis(max_markets: int) -> tuple[list[dict], list[dict]]:
    """Fetch markets via Synthesis API (unified Polymarket + Kalshi)."""
    with SynthesisClient() as client:
        # Fetch more events to get diversity (each event has many sub-markets)
        pm_events = client.get_polymarket_markets(limit=max(max_markets, 50))

        # Take top 1 sub-market per event (highest volume) for diversity
        markets = []
        for entry in pm_events:
            event = entry.get("event", {})
            sub_markets = entry.get("markets", [])
            event_slug = event.get("slug", "")

            if not sub_markets:
                continue

            # Sort sub-markets by volume, pick the top one per event
            sorted_subs = sorted(
                sub_markets,
                key=lambda x: float(x.get("volume", 0) or 0),
                reverse=True,
            )

            # Take top 1 from this event (the most traded outcome)
            m = sorted_subs[0]
            market_id = m.get("condition_id", m.get("slug", ""))
            if not market_id or not m.get("active", True):
                continue

            yes_price = float(m.get("left_price", 0.5))
            no_price = float(m.get("right_price", 1 - yes_price))

            markets.append({
                "id": market_id,
                "question": m.get("question", event.get("title", "")),
                "description": m.get("description", event.get("description", "")),
                "slug": m.get("slug", ""),
                "event_slug": event_slug,
                "outcome": m.get("outcome", ""),
                "left_token_id": m.get("left_token_id", ""),
                "right_token_id": m.get("right_token_id", ""),
                "yes_odds": yes_price,
                "no_odds": no_price,
                "outcomes": [m.get("left_outcome", "Yes"), m.get("right_outcome", "No")],
                "volume": float(m.get("volume", 0) or 0),
                "liquidity": float(m.get("liquidity", 0) or 0),
                "end_date": event.get("ends_at", ""),
                "active": m.get("active", True),
                "closed": False,
                "resolved": m.get("resolved", False),
                "resolution": None,
                "venue": "polymarket",
                "synthesis_url": f"https://synthesis.trade/market/{event_slug}",
            })

        # Filter out extreme tail markets (< 10% or > 90% odds have no edge potential)
        markets = [m for m in markets if 0.10 <= m["yes_odds"] <= 0.90]

        # Sort by volume, take top N
        markets.sort(key=lambda x: x["volume"], reverse=True)
        markets = markets[:max_markets]

        # Fetch and flatten Kalshi markets for cross-platform arb
        raw_kalshi = client.get_kalshi_markets(limit=50)
        kalshi_markets = []
        for entry in raw_kalshi:
            event = entry.get("event", {})
            for m in entry.get("markets", []):
                if not m.get("active", True):
                    continue
                yes_price = float(m.get("left_price", 0.5))
                if not (0.10 <= yes_price <= 0.90):
                    continue
                kalshi_markets.append({
                    "id": m.get("market_id", m.get("kalshi_id", "")),
                    "question": m.get("title", ""),
                    "outcome": m.get("outcome", ""),
                    "yes_odds": yes_price,
                    "yes_price": yes_price,
                    "no_odds": float(m.get("right_price", 1 - yes_price)),
                    "volume": float(m.get("volume", 0) or 0),
                    "event_ticker": m.get("event_id", ""),
                    "venue": "kalshi",
                })

        client.save_snapshot(markets)

    return markets, kalshi_markets


def _fetch_markets_direct(max_markets: int) -> tuple[list[dict], list[dict]]:
    """Fetch markets directly from Polymarket API (fallback)."""
    with PolymarketClient() as client:
        markets = client.get_active_markets(limit=max_markets)
        client.save_snapshot(markets)
    return markets, []


def _update_status(step: int, total: int, label: str, detail: str = "", **extra):
    """Write pipeline status to file for dashboard polling."""
    status = {
        "step": step,
        "total_steps": total,
        "label": label,
        "detail": detail,
        "progress": round(step / total * 100),
        "running": step < total,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
    status_path = DATA_DIR / "pipeline_status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(_json.dumps(status, indent=2))


def run_pipeline(
    max_markets: int = MAX_MARKETS,
    run_backtest_flag: bool = False,
    trade_flag: bool = False,
    export: bool = True,
    use_cache: bool = True,
) -> dict:
    """Execute the full signal generation pipeline.

    Uses Synthesis API if SYNTHESIS_API_KEY is set,
    otherwise falls back to direct Polymarket API.
    """
    start_time = time.time()
    use_synthesis = bool(SYNTHESIS_API_KEY)

    STEPS = 7
    print("\n=== Polymarket Signal Agent ===")
    if use_synthesis:
        print(">>> Powered by Synthesis.trade API <<<")
    print(f"Started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Max markets: {max_markets}\n")

    _update_status(0, STEPS, "Starting pipeline", f"Max markets: {max_markets}")

    # Step 1: Fetch markets
    if use_synthesis:
        _update_status(1, STEPS, "Fetching markets", "Connecting to Synthesis.trade API (Polymarket + Kalshi)")
        print("[1/6] Fetching markets via Synthesis API (Polymarket + Kalshi)...")
        markets, kalshi_markets = _fetch_markets_synthesis(max_markets)
    else:
        print("[1/6] Fetching active markets from Polymarket...")
        markets, kalshi_markets = _fetch_markets_direct(max_markets)

    if not markets:
        print("No active markets found. Exiting.")
        return {"signals": [], "metrics": None}
    print(f"  Found {len(markets)} markets\n")

    # Step 2: Fetch news
    _update_status(2, STEPS, "Gathering news", f"Searching Google News for {len(markets)} markets")
    print("[2/6] Gathering news for each market...")
    news_map: dict[str, list[dict]] = {}
    for i, market in enumerate(markets, 1):
        sys.stdout.write(f"\r  Fetching news: {i}/{len(markets)}")
        sys.stdout.flush()
        news = fetch_news_for_market(market, use_cache=use_cache)
        news_map[market["id"]] = news
    print(f"\n  News gathered for {len(news_map)} markets\n")

    # Step 3: LLM analysis
    if not GROQ_API_KEY:
        print("[3/6] WARNING: No GROQ_API_KEY set. Skipping LLM analysis.")
        analyses = [
            {
                "market_id": m["id"],
                "question": m["question"],
                "market_odds": m["yes_odds"],
                "probability": m["yes_odds"],
                "confidence": 0.1,
                "reasoning": "No LLM analysis available (API key not configured).",
                "key_factors": [],
            }
            for m in markets
        ]
    else:
        _update_status(3, STEPS, "LLM ensemble analysis", "Querying Llama 3.3 70B + Llama 3.1 8B + Qwen3 32B via Groq")
        print("[3/6] Running LLM ensemble analysis...")
        analyzer = LLMAnalyzer()
        analyses = analyzer.batch_analyze(markets, news_map)
    print(f"  Analyzed {len(analyses)} markets\n")

    # Step 4: Generate signals
    _update_status(4, STEPS, "Generating signals", "Edge calculation + Platt calibration + Kelly sizing")
    print("[4/6] Generating signals with Kelly sizing...")
    news_counts = {mid: len(articles) for mid, articles in news_map.items()}
    slugs = {m["id"]: m.get("slug", "") for m in markets}
    token_ids = {m["id"]: {"left": m.get("left_token_id", ""), "right": m.get("right_token_id", "")} for m in markets}
    signals = generate_all_signals(analyses, news_counts, slugs=slugs, token_ids=token_ids)
    print(f"  Generated {len(signals)} signals\n")

    # Step 5: Cross-platform arbitrage scan
    _update_status(5, STEPS, "Arbitrage scan", "Matching 1,400+ outcomes across Polymarket and Kalshi")
    print("[5/6] Scanning for arbitrage opportunities...")
    arb_result = scan_all_arbitrage(markets, kalshi_markets if kalshi_markets else None)

    # Cross-platform arb via Synthesis outcome matching
    if use_synthesis:
        print("  Running cross-platform outcome matching (Polymarket vs Kalshi)...")
        with SynthesisClient() as client:
            synthesis_arbs = client.detect_arbitrage(min_price_diff=0.02)
            if synthesis_arbs:
                arb_result["cross_platform"] = synthesis_arbs
                arb_result["total_opportunities"] += len(synthesis_arbs)

    print(f"  Found {arb_result['total_opportunities']} arbitrage opportunities\n")

    # Step 6: Export
    result = {"signals": signals, "metrics": None}

    if export:
        _update_status(6, STEPS, "Exporting results", "Saving signals + arbitrage to dashboard")
        print("[6/6] Exporting results...")
        filepath = export_signals(signals)
        print(f"  Signals exported to {filepath}\n")
    else:
        print("[6/6] Skipping export\n")

    print_signal_summary(signals)

    # Trading execution
    if trade_flag and use_synthesis:
        print("\n--- Trading Execution ---")
        from engine.trader import Trader
        try:
            with Trader() as trader:
                trader.full_setup()

                balance = trader.get_balance()
                print(f"  Wallet balance: {balance}")

                print(f"  Executing top {min(3, len(signals))} signals...")
                trade_results = trader.execute_signals(signals, max_orders=3, max_amount_per_order=2.0)
                for tr in trade_results:
                    status = "OK" if "error" not in tr["result"] else tr["result"].get("error", "")[:50]
                    print(f"    {tr['side']} ${tr['amount']} {tr['question'][:40]}... → {status}")

                trader.export_dashboard_data()
                print(f"  Positions: {len(trader.get_positions())}")
                print(f"  Trading data exported")
        except Exception as e:
            print(f"  Trading setup failed: {e}")
            print("  Signals were still generated and exported successfully.")
            print("  Check your SYNTHESIS_API_KEY in .env (needs Project Secret Key).")
    elif trade_flag and not use_synthesis:
        print("\n--- Trading requires SYNTHESIS_API_KEY ---")

    # Backtest
    if run_backtest_flag:
        print("\n--- Running Backtest ---")
        bt_result = run_backtest_from_history(signals)
        if bt_result:
            result["metrics"] = bt_result["metrics"]
            print_backtest_summary(bt_result["metrics"])
            if export:
                export_results(
                    bt_result["metrics"],
                    bt_result["pnl_curve"],
                    bt_result["trades"],
                )

    elapsed = time.time() - start_time
    actionable = len([s for s in signals if s["signal"] != "HOLD"])
    _update_status(STEPS, STEPS, "Pipeline complete",
                   f"{actionable} signals, {arb_result['total_opportunities']} arbitrage in {elapsed:.0f}s",
                   signals_count=len(signals), actionable=actionable,
                   arbitrage=arb_result["total_opportunities"], elapsed=round(elapsed, 1))
    print(f"\nPipeline completed in {elapsed:.1f}s")
    return result


def run_backtest_from_history(current_signals: list[dict]) -> dict | None:
    """Run backtest using resolved markets from historical data."""
    markets_data = load_latest_markets()
    if not markets_data:
        print("  No historical market data found for backtest.")
        return None

    resolutions = get_resolved_markets(markets_data)
    if not resolutions:
        print("  No resolved markets found. Loading seed data if available...")
        from engine.data_store import load_latest_backtest
        existing = load_latest_backtest()
        if existing:
            return existing
        return None

    bt = run_backtest(current_signals, resolutions)
    return bt


def main():
    parser = argparse.ArgumentParser(
        description="Polymarket Signal Agent - AI-powered prediction market signals"
    )
    parser.add_argument(
        "--markets", type=int, default=MAX_MARKETS,
        help=f"Maximum number of markets to analyze (default: {MAX_MARKETS})"
    )
    parser.add_argument(
        "--backtest", action="store_true",
        help="Run backtest after signal generation"
    )
    parser.add_argument(
        "--no-export", action="store_true",
        help="Skip exporting results to files"
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Disable news caching (re-fetch all)"
    )
    parser.add_argument(
        "--trade", action="store_true",
        help="Execute top signals as real orders via Synthesis"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    run_pipeline(
        max_markets=args.markets,
        run_backtest_flag=args.backtest,
        trade_flag=args.trade,
        export=not args.no_export,
        use_cache=not args.no_cache,
    )


if __name__ == "__main__":
    main()
