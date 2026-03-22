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


def run_pipeline(
    max_markets: int = MAX_MARKETS,
    run_backtest_flag: bool = False,
    export: bool = True,
    use_cache: bool = True,
) -> dict:
    """Execute the full signal generation pipeline.

    Uses Synthesis API if SYNTHESIS_API_KEY is set,
    otherwise falls back to direct Polymarket API.
    """
    start_time = time.time()
    use_synthesis = bool(SYNTHESIS_API_KEY)

    print("\n=== Polymarket Signal Agent ===")
    if use_synthesis:
        print(">>> Powered by Synthesis.trade API <<<")
    print(f"Started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Max markets: {max_markets}\n")

    # Step 1: Fetch markets
    if use_synthesis:
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
        print("[3/6] Running LLM ensemble analysis...")
        analyzer = LLMAnalyzer()
        analyses = analyzer.batch_analyze(markets, news_map)
    print(f"  Analyzed {len(analyses)} markets\n")

    # Step 4: Generate signals
    print("[4/6] Generating signals with Kelly sizing...")
    news_counts = {mid: len(articles) for mid, articles in news_map.items()}
    slugs = {m["id"]: m.get("slug", "") for m in markets}
    signals = generate_all_signals(analyses, news_counts, slugs=slugs)
    print(f"  Generated {len(signals)} signals\n")

    # Step 5: Cross-platform arbitrage scan
    print("[5/6] Scanning for arbitrage opportunities...")
    arb_result = scan_all_arbitrage(markets, kalshi_markets if kalshi_markets else None)
    print(f"  Found {arb_result['total_opportunities']} arbitrage opportunities\n")

    # Step 6: Export
    result = {"signals": signals, "metrics": None}

    if export:
        print("[6/6] Exporting results...")
        filepath = export_signals(signals)
        print(f"  Signals exported to {filepath}\n")
    else:
        print("[6/6] Skipping export\n")

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
