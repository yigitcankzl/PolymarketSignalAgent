"""Generate realistic demo/seed data for the dashboard."""

import json
import random
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

random.seed(42)

# Realistic market questions
MARKETS = [
    {"question": "Will the Fed cut interest rates at the June 2026 FOMC meeting?", "slug": "fed-rate-cut-june-2026", "category": "economics"},
    {"question": "Will Bitcoin exceed $150,000 by end of Q2 2026?", "slug": "bitcoin-150k-q2-2026", "category": "crypto"},
    {"question": "Will Trump win the 2028 Republican primary?", "slug": "trump-2028-republican-primary", "category": "politics"},
    {"question": "Will the US GDP growth exceed 3% in Q1 2026?", "slug": "us-gdp-growth-q1-2026", "category": "economics"},
    {"question": "Will SpaceX Starship complete an orbital flight by April 2026?", "slug": "spacex-starship-orbital-2026", "category": "tech"},
    {"question": "Will the S&P 500 reach 6500 by end of March 2026?", "slug": "sp500-6500-march-2026", "category": "markets"},
    {"question": "Will NVIDIA stock price exceed $200 by Q2 2026?", "slug": "nvidia-200-q2-2026", "category": "markets"},
    {"question": "Will the EU impose new AI regulations by mid-2026?", "slug": "eu-ai-regulations-2026", "category": "policy"},
    {"question": "Will OpenAI release GPT-5 by June 2026?", "slug": "openai-gpt5-june-2026", "category": "tech"},
    {"question": "Will there be a US government shutdown in Q2 2026?", "slug": "us-government-shutdown-q2-2026", "category": "politics"},
    {"question": "Will Ethereum merge to a new consensus mechanism in 2026?", "slug": "ethereum-consensus-2026", "category": "crypto"},
    {"question": "Will the US unemployment rate drop below 3.5%?", "slug": "us-unemployment-below-35", "category": "economics"},
    {"question": "Will Apple announce a foldable iPhone in 2026?", "slug": "apple-foldable-iphone-2026", "category": "tech"},
    {"question": "Will the Ukraine conflict reach a ceasefire by mid-2026?", "slug": "ukraine-ceasefire-mid-2026", "category": "geopolitics"},
    {"question": "Will Tesla deliver 2 million vehicles in 2026?", "slug": "tesla-2m-deliveries-2026", "category": "markets"},
    {"question": "Will the 2026 FIFA World Cup generate record viewership?", "slug": "fifa-2026-record-viewership", "category": "sports"},
    {"question": "Will Japan's Nikkei 225 reach 50,000 in 2026?", "slug": "nikkei-50k-2026", "category": "markets"},
    {"question": "Will a new COVID variant trigger WHO alert in 2026?", "slug": "covid-variant-who-2026", "category": "health"},
    {"question": "Will the US pass a federal privacy law by end of 2026?", "slug": "us-federal-privacy-law-2026", "category": "policy"},
    {"question": "Will Meta's Threads surpass 500M monthly active users?", "slug": "meta-threads-500m-mau", "category": "tech"},
    {"question": "Will India's GDP surpass Japan's in 2026?", "slug": "india-gdp-surpass-japan-2026", "category": "economics"},
    {"question": "Will the next Supreme Court vacancy occur before 2027?", "slug": "scotus-vacancy-before-2027", "category": "politics"},
    {"question": "Will Solana's price exceed $300 by Q3 2026?", "slug": "solana-300-q3-2026", "category": "crypto"},
    {"question": "Will global oil prices drop below $60/barrel?", "slug": "oil-below-60-barrel", "category": "commodities"},
    {"question": "Will a major tech company announce layoffs exceeding 10,000?", "slug": "tech-layoffs-10k-2026", "category": "tech"},
]


def generate_market(idx: int, m: dict, base_time: datetime) -> dict:
    market_odds = round(random.uniform(0.15, 0.88), 4)
    volume = round(random.uniform(50000, 5000000), 2)
    liquidity = round(volume * random.uniform(0.05, 0.3), 2)

    return {
        "id": f"market_{idx:04d}",
        "question": m["question"],
        "description": f"Market for predicting: {m['question']}",
        "slug": m["slug"],
        "yes_odds": market_odds,
        "no_odds": round(1 - market_odds, 4),
        "outcomes": ["Yes", "No"],
        "volume": volume,
        "liquidity": liquidity,
        "end_date": (base_time + timedelta(days=random.randint(30, 180))).isoformat(),
        "created_at": (base_time - timedelta(days=random.randint(10, 60))).isoformat(),
        "active": True,
        "closed": False,
        "resolved": idx < 18,  # first 18 markets are resolved (for backtest)
        "resolution": None,  # set after signal generation to correlate with LLM
    }


def _generate_sparkline(current_price: float, points: int = 20) -> list[float]:
    """Generate realistic-looking price sparkline data."""
    prices = []
    p = current_price + random.gauss(0, 0.08)
    for _ in range(points):
        p += random.gauss(0, 0.015)
        p = max(0.05, min(0.95, p))
        prices.append(round(p, 4))
    # Ensure last point is close to current price
    prices[-1] = current_price
    return prices


def generate_signal(market: dict, base_time: datetime, offset_hours: int) -> dict:
    market_odds = market["yes_odds"]

    # LLM probability deviates from market odds with wider spread for interesting signals
    deviation = random.gauss(0, 0.15)
    if abs(deviation) < 0.04:
        deviation = 0.08 * (1 if random.random() > 0.5 else -1)
    llm_prob = max(0.02, min(0.98, market_odds + deviation))
    confidence = round(random.uniform(0.45, 0.92), 4)
    edge = round(llm_prob - market_odds, 4)

    # Determine signal
    if edge > 0.10 and confidence > 0.5:
        signal = "STRONG_BUY"
    elif edge > 0.05 and confidence > 0.4:
        signal = "BUY"
    elif edge < -0.10 and confidence > 0.5:
        signal = "STRONG_SELL"
    elif edge < -0.05 and confidence > 0.4:
        signal = "SELL"
    else:
        signal = "HOLD"

    score = round(abs(edge) * confidence, 4)
    ts = base_time - timedelta(hours=offset_hours)

    reasonings = [
        "Recent economic data supports this direction. Market sentiment appears to be lagging behind fundamentals.",
        "News flow is strongly aligned with this position. Key stakeholder statements reinforce the thesis.",
        "Technical indicators and news sentiment diverge from current market pricing. Adjustment likely incoming.",
        "Fundamental analysis suggests mispricing. Multiple catalysts could trigger price movement.",
        "Mixed signals from news sources but weight of evidence leans toward this outcome. Confidence moderate.",
        "Strong institutional signals and policy direction support this view. Market has not fully priced in recent developments.",
        "Data-driven analysis indicates significant edge. Historical patterns support this directional view.",
    ]

    factors_pool = [
        "Recent economic indicators", "Policy announcements", "Market sentiment shift",
        "Institutional positioning", "Technical momentum", "Geopolitical developments",
        "Earnings data", "Regulatory signals", "Supply chain factors",
        "Consumer confidence data", "Central bank communications", "Trade flow changes",
        "Technology adoption rates", "Demographic trends", "Credit market conditions",
    ]

    # Kelly criterion
    kelly = 0.0
    if abs(edge) > 0.01 and confidence > 0.3:
        if edge > 0:
            p = min(0.95, market_odds + edge)
            b = (1 / market_odds) - 1 if market_odds > 0 else 0
        else:
            p = min(0.95, (1 - market_odds) + abs(edge))
            b = (1 / (1 - market_odds)) - 1 if market_odds < 1 else 0
        if b > 0:
            q = 1 - p
            kelly = max(0, ((p * b - q) / b) * 0.25 * confidence)
            kelly = min(kelly, 0.05)

    # Ensemble data (simulated)
    model_predictions = {
        "llama-3.3-70b-versatile": round(llm_prob + random.gauss(0, 0.03), 4),
        "llama-3.1-8b-instant": round(llm_prob + random.gauss(0, 0.05), 4),
        "gemma2-9b-it": round(llm_prob + random.gauss(0, 0.04), 4),
    }
    model_predictions = {k: max(0.02, min(0.98, v)) for k, v in model_predictions.items()}
    spread = max(model_predictions.values()) - min(model_predictions.values())

    return {
        "market_id": market["id"],
        "question": market["question"],
        "market_odds": market_odds,
        "llm_probability": round(llm_prob, 4),
        "raw_probability": round(llm_prob * 0.95 + 0.025, 4),  # pre-calibration
        "edge": edge,
        "confidence": confidence,
        "signal": signal,
        "score": score,
        "kelly_fraction": round(kelly, 4),
        "sparkline": _generate_sparkline(market_odds, 20),
        "polymarket_url": f"https://polymarket.com/event/{market.get('slug', '')}",
        "reasoning": random.choice(reasonings),
        "key_factors": random.sample(factors_pool, random.randint(3, 5)),
        "ensemble": {
            "models_used": 3,
            "model_predictions": model_predictions,
            "median": round(sorted(model_predictions.values())[1], 4),
            "spread": round(spread, 4),
            "calibrated": round(llm_prob, 4),
        },
        "timestamp": ts.isoformat(),
        "news_count": random.randint(3, 12),
    }


def generate_backtest_data(signals: list[dict], markets: list[dict]) -> dict:
    """Generate realistic backtest results."""
    resolved_markets = {m["id"]: m["resolution"] for m in markets if m.get("resolved") and m["resolution"] is not None}

    trades = []
    for sig in signals:
        mid = sig["market_id"]
        if mid not in resolved_markets or sig["signal"] == "HOLD":
            continue

        resolution = resolved_markets[mid]

        if sig["signal"] in ("STRONG_BUY", "BUY"):
            pnl = round(resolution - sig["market_odds"], 4)
            correct = resolution == 1.0
        else:
            pnl = round(sig["market_odds"] - resolution, 4)
            correct = resolution == 0.0

        trades.append({
            "market_id": mid,
            "question": sig["question"],
            "signal": sig["signal"],
            "market_odds": sig["market_odds"],
            "llm_probability": sig["llm_probability"],
            "edge": sig["edge"],
            "confidence": sig["confidence"],
            "resolution": resolution,
            "pnl": pnl,
            "correct": correct,
            "timestamp": sig["timestamp"],
        })

    # Calculate metrics
    if not trades:
        return {"trades": [], "metrics": {}, "pnl_curve": []}

    total = len(trades)
    correct_count = sum(1 for t in trades if t["correct"])
    pnls = [t["pnl"] for t in trades]
    total_pnl = sum(pnls)
    winning = [p for p in pnls if p > 0]
    losing = [p for p in pnls if p < 0]

    hit_rate = correct_count / total
    avg_return = total_pnl / total
    if len(pnls) > 1:
        std_return = (sum((p - avg_return) ** 2 for p in pnls) / (len(pnls) - 1)) ** 0.5
        sharpe = (avg_return / std_return * math.sqrt(252)) if std_return > 0 else 0
    else:
        sharpe = 0

    # Max drawdown
    cum = 0
    peak = 0
    max_dd = 0
    for p in pnls:
        cum += p
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > max_dd:
            max_dd = dd

    gross_profit = sum(winning) if winning else 0
    gross_loss = abs(sum(losing)) if losing else 0.001

    signal_stats = {}
    for t in trades:
        s = t["signal"]
        if s not in signal_stats:
            signal_stats[s] = {"total": 0, "correct": 0}
        signal_stats[s]["total"] += 1
        if t["correct"]:
            signal_stats[s]["correct"] += 1

    metrics = {
        "total_signals": total,
        "correct_signals": correct_count,
        "hit_rate": round(hit_rate, 4),
        "total_pnl": round(total_pnl, 4),
        "avg_pnl": round(avg_return, 4),
        "avg_edge": round(sum(t["edge"] for t in trades) / total, 4),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": round(max_dd, 4),
        "profit_factor": round(gross_profit / gross_loss, 4),
        "win_count": len(winning),
        "loss_count": len(losing),
        "best_trade": round(max(pnls), 4),
        "worst_trade": round(min(pnls), 4),
        "win_rate_by_signal": {
            s: round(d["correct"] / d["total"], 4) for s, d in signal_stats.items()
        },
    }

    # PnL curve
    cumulative = 0
    pnl_curve = []
    for i, t in enumerate(trades):
        cumulative += t["pnl"]
        pnl_curve.append({
            "trade_number": i + 1,
            "market_id": t["market_id"],
            "question": t["question"][:50],
            "signal": t["signal"],
            "pnl": t["pnl"],
            "cumulative_pnl": round(cumulative, 4),
            "timestamp": t["timestamp"],
        })

    return {"trades": trades, "metrics": metrics, "pnl_curve": pnl_curve}


def main():
    base_time = datetime(2026, 3, 22, 12, 0, 0, tzinfo=timezone.utc)

    # Generate markets
    markets = [generate_market(i, m, base_time) for i, m in enumerate(MARKETS)]

    markets_data = {
        "timestamp": base_time.strftime("%Y%m%dT%H%M%SZ"),
        "count": len(markets),
        "markets": markets,
    }

    # Generate signals (one per market)
    signals = []
    for i, market in enumerate(markets):
        sig = generate_signal(market, base_time, offset_hours=i * 2)
        signals.append(sig)

    # Set resolutions that correlate with signal direction (system has edge)
    for i, market in enumerate(markets):
        if not market["resolved"]:
            continue
        sig = signals[i]
        signal_type = sig["signal"]
        # System is right ~62% of the time on actionable signals
        if signal_type in ("STRONG_BUY", "BUY"):
            market["resolution"] = 1.0 if random.random() < 0.64 else 0.0
        elif signal_type in ("STRONG_SELL", "SELL"):
            market["resolution"] = 0.0 if random.random() < 0.64 else 1.0
        else:
            market["resolution"] = 1.0 if random.random() < 0.5 else 0.0

    # Update markets_data after setting resolutions
    markets_data["markets"] = markets

    signals.sort(key=lambda s: s["score"], reverse=True)

    signals_data = {
        "generated_at": base_time.isoformat(),
        "total_signals": len(signals),
        "actionable_signals": len([s for s in signals if s["signal"] != "HOLD"]),
        "signals": signals,
    }

    # Generate backtest
    backtest_data = generate_backtest_data(signals, markets)
    backtest_data["run_at"] = base_time.isoformat()

    # Generate arbitrage opportunities
    arb_data = {
        "scanned_at": base_time.isoformat(),
        "markets_scanned": len(markets),
        "intra_market": [
            {
                "type": "intra_market",
                "market_id": markets[5]["id"],
                "question": markets[5]["question"],
                "yes_price": round(markets[5]["yes_odds"], 4),
                "no_price": round(1 - markets[5]["yes_odds"] - 0.03, 4),
                "total_cost": round(markets[5]["yes_odds"] + (1 - markets[5]["yes_odds"] - 0.03), 4),
                "guaranteed_profit_pct": 3.0,
                "slug": markets[5].get("slug", ""),
                "timestamp": base_time.isoformat(),
            },
        ],
        "related_market": [
            {
                "type": "related_market",
                "market_1": {"id": markets[0]["id"], "question": markets[0]["question"], "odds": markets[0]["yes_odds"]},
                "market_2": {"id": markets[3]["id"], "question": markets[3]["question"], "odds": markets[3]["yes_odds"]},
                "odds_difference": round(abs(markets[0]["yes_odds"] - markets[3]["yes_odds"]), 4),
                "overlap_score": 0.42,
                "timestamp": base_time.isoformat(),
            },
        ],
        "cross_platform": [
            {
                "type": "cross_platform",
                "polymarket": {
                    "id": markets[0]["id"],
                    "question": markets[0]["question"],
                    "yes_price": markets[0]["yes_odds"],
                    "slug": markets[0]["slug"],
                },
                "kalshi": {
                    "id": "FED-RATE-CUT-JUN26",
                    "question": "Fed to cut rates at June 2026 FOMC?",
                    "yes_price": round(markets[0]["yes_odds"] + 0.07, 4),
                    "event_ticker": "FED-RATE-CUT",
                },
                "price_difference": 0.07,
                "profit_potential_pct": 7.0,
                "similarity_score": 0.72,
                "action": "BUY on Polymarket, SELL on Kalshi",
                "buy_platform": "polymarket",
                "sell_platform": "kalshi",
                "buy_price": markets[0]["yes_odds"],
                "sell_price": round(markets[0]["yes_odds"] + 0.07, 4),
                "synthesis_url": f"https://synthesis.trade/market/{markets[0]['slug']}",
                "timestamp": base_time.isoformat(),
            },
            {
                "type": "cross_platform",
                "polymarket": {
                    "id": markets[1]["id"],
                    "question": markets[1]["question"],
                    "yes_price": markets[1]["yes_odds"],
                    "slug": markets[1]["slug"],
                },
                "kalshi": {
                    "id": "BTC-150K-Q2-26",
                    "question": "Bitcoin above $150,000 by June 30, 2026?",
                    "yes_price": round(markets[1]["yes_odds"] - 0.05, 4),
                    "event_ticker": "BTC-150K",
                },
                "price_difference": 0.05,
                "profit_potential_pct": 5.0,
                "similarity_score": 0.65,
                "action": "BUY on Kalshi, SELL on Polymarket",
                "buy_platform": "kalshi",
                "sell_platform": "polymarket",
                "buy_price": round(markets[1]["yes_odds"] - 0.05, 4),
                "sell_price": markets[1]["yes_odds"],
                "synthesis_url": f"https://synthesis.trade/market/{markets[1]['slug']}",
                "timestamp": base_time.isoformat(),
            },
            {
                "type": "cross_platform",
                "polymarket": {
                    "id": markets[4]["id"],
                    "question": markets[4]["question"],
                    "yes_price": markets[4]["yes_odds"],
                    "slug": markets[4]["slug"],
                },
                "kalshi": {
                    "id": "SPACEX-ORBITAL-APR26",
                    "question": "SpaceX orbital Starship flight before May 2026?",
                    "yes_price": round(markets[4]["yes_odds"] + 0.09, 4),
                    "event_ticker": "SPACEX-ORBITAL",
                },
                "price_difference": 0.09,
                "profit_potential_pct": 9.0,
                "similarity_score": 0.58,
                "action": "BUY on Polymarket, SELL on Kalshi",
                "buy_platform": "polymarket",
                "sell_platform": "kalshi",
                "buy_price": markets[4]["yes_odds"],
                "sell_price": round(markets[4]["yes_odds"] + 0.09, 4),
                "synthesis_url": f"https://synthesis.trade/market/{markets[4]['slug']}",
                "timestamp": base_time.isoformat(),
            },
        ],
        "kalshi_markets_scanned": 45,
        "total_opportunities": 5,
    }

    # Save everything
    for subdir in ["markets", "signals", "backtest", "arbitrage"]:
        (DATA_DIR / subdir).mkdir(parents=True, exist_ok=True)

    (DATA_DIR / "markets" / "latest.json").write_text(json.dumps(markets_data, indent=2))
    (DATA_DIR / "signals" / "latest.json").write_text(json.dumps(signals_data, indent=2))
    (DATA_DIR / "backtest" / "latest.json").write_text(json.dumps(backtest_data, indent=2))
    (DATA_DIR / "arbitrage" / "latest.json").write_text(json.dumps(arb_data, indent=2))

    print(f"Seed data generated:")
    print(f"  Markets:  {len(markets)}")
    print(f"  Signals:  {len(signals)} ({signals_data['actionable_signals']} actionable)")
    print(f"  Trades:   {len(backtest_data['trades'])}")
    print(f"  Hit Rate: {backtest_data['metrics'].get('hit_rate', 0):.1%}")
    print(f"  Total PnL: {backtest_data['metrics'].get('total_pnl', 0):+.4f}")
    print(f"\nFiles saved to {DATA_DIR}/")


if __name__ == "__main__":
    main()
