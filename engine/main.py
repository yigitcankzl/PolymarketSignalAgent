"""CLI entry point - runs the full signal pipeline."""

import argparse
import logging
import sys
import time
from datetime import datetime, timezone

from engine.config import MAX_MARKETS, NEWS_HOURS_BACK, GROQ_API_KEY
from engine.polymarket_client import PolymarketClient
from engine.news_fetcher import fetch_news_for_market
from engine.llm_analyzer import LLMAnalyzer
from engine.signal_generator import generate_all_signals, export_signals, print_signal_summary
from engine.backtester import run_backtest, export_results, print_backtest_summary
from engine.data_store import load_latest_signals, get_resolved_markets, load_latest_markets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline(
    max_markets: int = MAX_MARKETS,
    run_backtest_flag: bool = False,
    export: bool = True,
    use_cache: bool = True,
) -> dict:
    """Execute the full signal generation pipeline.

    Steps:
    1. Fetch active markets from Polymarket
    2. Gather news for each market
    3. Analyze with LLM for probability estimates
    4. Calculate edge and generate signals
    5. Export results
    6. Optionally run backtest
    """
    start_time = time.time()
    print("\n=== Polymarket Signal Agent ===")
    print(f"Started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Max markets: {max_markets}\n")

    # Step 1: Fetch markets
    print("[1/5] Fetching active markets from Polymarket...")
    with PolymarketClient() as client:
        markets = client.get_active_markets(limit=max_markets)
        if not markets:
            print("No active markets found. Exiting.")
            return {"signals": [], "metrics": None}

        print(f"  Found {len(markets)} markets\n")
        client.save_snapshot(markets)

    # Step 2: Fetch news
    print("[2/5] Gathering news for each market...")
    news_map: dict[str, list[dict]] = {}
    for i, market in enumerate(markets, 1):
        sys.stdout.write(f"\r  Fetching news: {i}/{len(markets)}")
        sys.stdout.flush()
        news = fetch_news_for_market(market, use_cache=use_cache)
        news_map[market["id"]] = news
    print(f"\n  News gathered for {len(news_map)} markets\n")

    # Step 3: LLM analysis
    if not GROQ_API_KEY:
        print("[3/5] WARNING: No GROQ_API_KEY set. Skipping LLM analysis.")
        print("  Set GROQ_API_KEY in .env to enable AI-powered probability estimation.")
        # Generate dummy analyses
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
        print("[3/5] Running LLM analysis...")
        analyzer = LLMAnalyzer()
        analyses = analyzer.batch_analyze(markets, news_map)
    print(f"  Analyzed {len(analyses)} markets\n")

    # Step 4: Generate signals
    print("[4/5] Generating signals...")
    news_counts = {mid: len(articles) for mid, articles in news_map.items()}
    slugs = {m["id"]: m.get("slug", "") for m in markets}
    signals = generate_all_signals(analyses, news_counts, slugs=slugs)
    print(f"  Generated {len(signals)} signals\n")

    # Step 5: Export
    result = {"signals": signals, "metrics": None}

    if export:
        print("[5/5] Exporting results...")
        filepath = export_signals(signals)
        print(f"  Signals exported to {filepath}\n")
    else:
        print("[5/5] Skipping export\n")

    # Print summary
    print_signal_summary(signals)

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
        # Try loading from backtest/latest.json (seed data)
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
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    run_pipeline(
        max_markets=args.markets,
        run_backtest_flag=args.backtest,
        export=not args.no_export,
        use_cache=not args.no_cache,
    )


if __name__ == "__main__":
    main()
