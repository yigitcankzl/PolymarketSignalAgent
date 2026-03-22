# Architecture

## System Overview

The Polymarket Signal Agent is a 6-step pipeline that ingests prediction market data from Polymarket and Kalshi via the Synthesis.trade unified API, applies multi-LLM analysis with probability calibration, generates trading signals with risk-adjusted sizing, detects cross-platform arbitrage opportunities, and optionally executes trades — all orchestrated from a single CLI command.

Every component uses **live API data** — no mock data in the signal or arbitrage pipeline.

## Pipeline Flow

```
Step 1: MARKET FETCH                  Step 2: NEWS GATHERING
┌──────────────────────────┐          ┌──────────────────────┐
│  Synthesis.trade API     │          │  Google News RSS     │
│                          │          │                      │
│  GET /polymarket/markets │──────────│  Keyword extraction  │
│  GET /kalshi/markets     │          │  from market question│
│                          │          │                      │
│  50 events → flatten     │          │  Dedup + cache       │
│  Filter 10-90% odds      │          │  48h time window     │
│  Top N by volume         │          └──────────┬───────────┘
└──────────┬───────────────┘                     │
           │                                      │
           ▼                                      ▼
Step 3: LLM ENSEMBLE ANALYSIS
┌─────────────────────────────────────────────────────────┐
│  3 models queried in parallel via Groq API:             │
│                                                         │
│  ┌─────────────────┐ ┌───────────────┐ ┌─────────────┐ │
│  │ Llama 3.3 70B   │ │ Llama 3.1 8B  │ │ Qwen3 32B   │ │
│  │ (primary)       │ │ (fast)        │ │ (diverse)    │ │
│  └────────┬────────┘ └──────┬────────┘ └──────┬──────┘ │
│           │                 │                  │        │
│           └─────────────────┼──────────────────┘        │
│                             │                           │
│                      Median Probability                 │
│                             │                           │
│                   Platt Scaling (α=1.5)                 │
│                   Calibrated Probability                │
│                             │                           │
│  Superforecaster prompt:    │  Output:                  │
│  1. Base rate analysis      │  - probability (0-1)      │
│  2. Evidence for/against    │  - confidence (0-1)       │
│  3. Adjust from base rate   │  - reasoning (CoT)        │
│  4. Decisive estimation     │  - key_factors            │
└─────────────────────────────┼───────────────────────────┘
                              │
                              ▼
Step 4: SIGNAL GENERATION
┌───────────────────────────────────────────────────────────┐
│  Edge = Calibrated_LLM_Probability − Market_Odds          │
│                                                           │
│  ┌─────────────┬───────────────────────────────────────┐  │
│  │ Edge > +10% │ + Confidence > 50% → STRONG_BUY       │  │
│  │ Edge > +5%  │ + Confidence > 40% → BUY              │  │
│  │ Edge < -5%  │ + Confidence > 40% → SELL             │  │
│  │ Edge < -10% │ + Confidence > 50% → STRONG_SELL      │  │
│  │ Otherwise   │                    → HOLD             │  │
│  └─────────────┴───────────────────────────────────────┘  │
│                                                           │
│  Score = |edge| × confidence  (for ranking)               │
│  Kelly = fractional Kelly, quarter-sized, 5% max cap      │
└───────────────────────────────┬───────────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
Step 5: ARBITRAGE SCAN    TRADE EXECUTION    Step 6: EXPORT
┌──────────────────┐   ┌──────────────────┐ ┌────────────┐
│ Fetch 664 PM     │   │ Synthesis.trade  │ │ JSON files │
│ + 709 KA outcomes│   │ Wallet API       │ │ → Dashboard│
│                  │   │                  │ │            │
│ Match by outcome │   │ Account setup    │ │ signals/   │
│ name across      │   │ Wallet creation  │ │ markets/   │
│ platforms        │   │ Order placement  │ │ arbitrage/ │
│                  │   │ Position/PnL     │ │ trader/    │
│ Verify same event│   │ tracking         │ │            │
│ via title sim    │   │                  │ │ 7 API      │
│                  │   │ Kelly-sized      │ │ endpoints  │
│ 8 verified arb   │   │ market orders    │ │            │
│ opportunities    │   │                  │ │ Auto-      │
│                  │   │                  │ │ refresh    │
│ Synthesis.trade  │   │                  │ │ dashboard  │
│ links            │   │                  │ │            │
└──────────────────┘   └──────────────────┘ └────────────┘
```

## Module Responsibilities

### Synthesis Client (`synthesis_client.py`)
**Primary data layer** — all market data flows through Synthesis.trade's unified API:
- `get_polymarket_markets()` — fetches events with nested sub-markets
- `get_kalshi_markets()` — same format for Kalshi
- `search_markets(query, venue)` — cross-platform market search
- `detect_arbitrage()` — outcome-based cross-platform arbitrage detection
  - Builds flat outcome maps from both platforms (664 PM + 709 KA)
  - Matches by outcome name (e.g., "Buffalo Sabres" exists on both)
  - Verifies events are the same via normalized title similarity
  - Filters false positives (same team, different competition)

### Trader (`trader.py`)
**Automated trading** via Synthesis.trade wallet and order API:
- `full_setup()` — creates account → API key → wallet in sequence
- `place_order(token_id, side, amount)` — market/limit/stoploss orders
- `execute_signals(signals)` — auto-trades top signals with Kelly sizing
- `get_balance()`, `get_positions()`, `get_pnl()` — live portfolio state
- Persistent state in `data/trader/state.json` (survives restarts)

### LLM Analyzer (`llm_analyzer.py`)
**Multi-model ensemble** with calibration:
- Queries 3 Groq models: Llama 3.3 70B (primary), Llama 3.1 8B (fast), Qwen3 32B (diverse)
- Takes **median** probability for robustness
- **Platt scaling**: `P_cal = 1/(1+exp(-1.5×logit(P)))` — fixes RLHF hedging bias
- **Superforecaster prompting**: base rate decomposition, evidence weighing, decisive estimation
- Model disagreement (spread) automatically reduces confidence
- Robust JSON parsing: direct → code block → regex → fallback
- `<think>` tag stripping for reasoning models (Qwen)

### Signal Generator (`signal_generator.py`)
- Edge = calibrated LLM probability − market odds
- Five-tier classification with configurable thresholds
- **Kelly criterion**: `kelly = (p×b−q)/b × 0.25`, capped at 5% of bankroll
- Score-based ranking: `|edge| × confidence`
- Polymarket URL generation via event slug

### Arbitrage Scanner (`arbitrage.py`)
Three detection modes:
1. **Intra-market**: YES + NO < $1.00 (guaranteed profit)
2. **Related-market**: Similar questions on same platform with price discrepancy
3. **Cross-platform**: Same outcome on Polymarket vs Kalshi at different prices
   - Uses Synthesis API to fetch from both platforms
   - Event title similarity verification to avoid false matches

### News Fetcher (`news_fetcher.py`)
- Extracts keywords from market questions (stop word removal)
- Google News RSS (primary, no rate limits)
- Title-hash deduplication
- File-based caching (6h TTL) to avoid redundant fetches

### Backtester (`backtester.py`)
- Per-trade PnL based on signal direction and market resolution
- Metrics: hit rate, Sharpe ratio, max drawdown, profit factor
- Per-signal-type win rate breakdown
- Cumulative PnL curve for charting

## Data Flow

```
Live APIs                          Engine                    Dashboard
─────────                          ──────                    ─────────
Synthesis.trade ──→ markets ──→ data/markets/latest.json ──→ /api/markets
                               data/signals/latest.json ──→ /api/signals
Groq API ──→ LLM analysis ──→ (embedded in signals)
                               data/arbitrage/latest.json──→ /api/arbitrage
Google RSS ──→ news ──→ data/news/ (cached)
                               data/trader/latest.json ──→ /api/trading
Synthesis Wallet ──→ balance ──→ (embedded in trader data)
                               data/backtest/latest.json──→ /api/backtest
```

Dashboard auto-refreshes every 30 seconds. Toast notifications alert on new signals.

## Design Decisions

### Why Synthesis.trade?
- **Single API** for both Polymarket (Polygon) and Kalshi (Solana) — no need to manage two integrations
- **Cross-platform arbitrage** becomes trivial when both datasets come from one source
- **Trading execution** through the same API that provides market data
- **Wallet abstraction** — handles cross-chain deposits, bridging, and settlement

### Why 3-model ensemble?
- Diversity reduces individual model bias (70B + 8B + 32B, three architectures)
- Median aggregation is robust to one model being wrong
- Free tier across all models (Groq)
- Research: LLM ensembles match human forecaster accuracy (*Science Advances*, 2024)

### Why Platt scaling?
- LLMs trained with RLHF systematically hedge toward 0.5
- Platt scaling with α=1.5 pushes 0.6→0.65, 0.7→0.78, 0.8→0.87
- More decisive probabilities produce larger, more profitable edges
- Calibration is the single highest-impact improvement per research (AIA Forecaster, 2025)

### Why Kelly criterion?
- Optimal position sizing given estimated edge and confidence
- Quarter Kelly (0.25×) provides safety margin for estimation errors
- 5% cap prevents catastrophic loss on any single market
- Naturally sizes up on high-confidence, high-edge signals

## Rate Limits & Performance

| Component | Limit | Mitigation |
|-----------|-------|------------|
| Synthesis.trade | Generous | Primary data source |
| Groq API | 100K TPD (free) | 2.5s sleep, model fallback |
| Google RSS | None | Primary news source |

Pipeline runtime for 10 markets: ~110 seconds (with rate limiting).

## What's Real vs Simulated

| Component | Status | Source |
|-----------|--------|--------|
| Market prices | **Live** | Synthesis.trade API |
| News articles | **Live** | Google News RSS |
| LLM analysis | **Live** | Groq API (3-model ensemble) |
| Signal generation | **Live** | Computed from live data |
| Cross-platform arbitrage | **Live** | Synthesis API (664+709 outcomes) |
| Trading account + wallet | **Live** | Synthesis API |
| Backtest metrics | **Simulated** | Seed data (no resolved markets yet) |
