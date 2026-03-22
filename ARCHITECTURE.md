# Architecture

## System Overview

The Polymarket Signal Agent is a pipeline-based system that generates trading signals for prediction markets. It follows a sequential data flow pattern where each stage transforms and enriches data before passing it to the next.

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SIGNAL PIPELINE                             │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐    │
│  │  Polymarket   │──→│    News      │──→│     LLM Analyzer     │    │
│  │   Client      │   │   Fetcher    │   │   (Groq/Llama 3.3)  │    │
│  │              │   │              │   │                      │    │
│  │ gamma-api    │   │ Google RSS   │   │ System + User prompt │    │
│  │ /markets     │   │ NewsData.io  │   │ JSON probability out │    │
│  └──────┬───────┘   └──────────────┘   └──────────┬───────────┘    │
│         │                                          │                │
│         │          ┌──────────────┐                │                │
│         └─────────→│   Signal     │←───────────────┘                │
│                    │  Generator   │                                  │
│                    │              │                                  │
│                    │ edge = LLM   │                                  │
│                    │   - market   │                                  │
│                    └──────┬───────┘                                  │
│                           │                                         │
│              ┌────────────┼────────────┐                            │
│              ▼            ▼            ▼                            │
│        ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│        │  Export   │ │ Backtest │ │ Dashboard│                      │
│        │  (JSON)  │ │  Engine  │ │ (Next.js)│                      │
│        └──────────┘ └──────────┘ └──────────┘                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### 1. Polymarket Client (`polymarket_client.py`)
- Connects to Polymarket's gamma API (`https://gamma-api.polymarket.com`)
- Fetches active markets, filters by volume threshold
- Parses `outcomePrices` JSON string to extract Yes/No odds
- Saves market snapshots with timestamps for historical tracking

### 2. News Fetcher (`news_fetcher.py`)
- Extracts search keywords from market questions (stop word removal)
- Fetches from Google News RSS (primary, unlimited)
- Optional: NewsData.io API (secondary, rate-limited)
- Deduplicates articles by title hash
- Filters by time window (configurable, default 48h)
- Caches results to avoid redundant API calls

### 3. LLM Analyzer (`llm_analyzer.py`)
- **Multi-LLM Ensemble**: Queries 3 Groq models (Llama 3.3 70B, Llama 3.1 8B, Gemma2 9B)
- **Superforecaster Prompting**: Tetlock-style methodology with base rate decomposition, evidence weighing, and decisive estimation
- **Median Aggregation**: Takes median probability across models for robustness
- **Platt Scaling Calibration**: `P_cal = 1/(1+exp(-alpha*logit(P)))` with alpha=1.5 to fix LLM hedging bias
- **Confidence Adjustment**: Model disagreement (spread) reduces confidence automatically
- Returns: probability, confidence, reasoning, key_factors, ensemble metadata
- Rate limiting: 2.5s between requests (30 RPM Groq limit)
- Robust JSON parsing with regex fallbacks
- Graceful fallback to market odds on total failure

### 4. Signal Generator (`signal_generator.py`)
- **Edge Formula**: `edge = calibrated_llm_probability - market_odds`
- Five-tier classification: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
- **Score**: `abs(edge) * confidence` for ranking
- **Kelly Criterion**: Fractional Kelly (quarter, 5% cap) position sizing per signal
- **Polymarket Links**: Direct URL to market page via slug
- Exports to JSON with `latest.json` for dashboard consumption

### 4b. Arbitrage Scanner (`arbitrage.py`)
- **Intra-market**: Detects when YES + NO best prices < $1.00 (guaranteed profit)
- **Related-market**: Finds pricing discrepancies between similar questions via keyword overlap
- Results exported to `data/arbitrage/latest.json`

### 5. Backtester (`backtester.py`)
- PnL calculation per trade based on signal direction and resolution
- Comprehensive metrics: hit rate, Sharpe ratio, max drawdown, profit factor
- Per-signal-type win rate breakdown
- Cumulative PnL curve generation for charting

### 6. Data Store (`data_store.py`)
- Simple JSON file-based persistence
- Convention: each module writes to its `data/` subdirectory
- `latest.json` files serve as the API contract with the dashboard

## Data Flow: Engine → Dashboard

The dashboard reads from the engine's output files. No database or message queue is needed.

```
Engine writes:                    Dashboard reads:
data/signals/latest.json    ←──  /api/signals (GET)
data/markets/latest.json    ←──  /api/markets (GET)
data/backtest/latest.json   ←──  /api/backtest (GET)
data/arbitrage/latest.json  ←──  /api/arbitrage (GET)
```

API routes are simple `fs.readFile` operations that return JSON. The dashboard auto-refreshes every 30 seconds with a countdown timer and toast notifications for new signals.

## Design Decisions

### Why Groq with 3-model ensemble?
- Free tier with generous limits (30 RPM, 14400 RPD)
- 3 diverse models (70B, 8B, 9B) provide ensemble diversity at zero cost
- Median aggregation is robust to individual model errors
- Research shows LLM ensembles match human forecaster accuracy (Science Advances, 2024)
- OpenAI-compatible API means easy migration to other providers

### Why JSON files instead of a database?
- Zero infrastructure overhead
- Human-readable output for debugging
- Easy to version control sample data
- Dashboard can read directly without an ORM layer
- Sufficient for a pipeline that runs hourly/daily

### Why server-side data fetching in API routes?
- Data files live on the same machine as the dashboard
- No CORS issues
- Clean separation: engine writes, dashboard reads
- Easy to extend with caching headers later

### Why Recharts over Plotly/D3?
- Native React integration
- Works seamlessly with shadcn/ui patterns
- Lightweight bundle size
- Sufficient for the chart types needed (area, bar)

## Edge Calculation Theory

The system's core hypothesis: **LLM ensembles with calibrated probabilities can detect information edges in prediction markets by synthesizing recent news faster than the market can price it in.**

```
Raw Probability = median(Model1, Model2, Model3)
Calibrated P    = 1 / (1 + exp(-1.5 * logit(Raw P)))     # Platt scaling
Edge            = Calibrated P - Market Odds
Kelly Size      = (edge * confidence) / odds * 0.25       # Quarter Kelly, capped at 5%
```

The calibration step is critical: LLMs trained with RLHF tend to hedge toward 0.5. Platt scaling with alpha=1.5 pushes a hedged 0.6 → 0.65 and 0.7 → 0.78, producing more decisive and profitable signals.

The system is most valuable when:
1. News breaks that hasn't been reflected in market prices yet
2. Multiple models agree on direction (low ensemble spread)
3. The confidence is high enough to filter noise from signal
4. Kelly sizing prevents overexposure to any single market

## Rate Limits & Performance

| Component | Limit | Mitigation |
|-----------|-------|------------|
| Groq API | 30 RPM | 2.5s sleep between requests |
| Google RSS | None | Primary news source |
| NewsData.io | 200/day | Secondary, optional |
| Polymarket | None (public) | Basic httpx timeouts |

For 30 markets with ensemble enabled, the full pipeline takes approximately:
- Market fetch: ~2s
- News fetch: ~30s (parallel-capable, currently sequential)
- LLM ensemble analysis: ~225s (30 markets * 3 models * 2.5s rate limit)
- Signal generation + arbitrage scan: <1s
- **Total: ~4.5 minutes**

With ensemble disabled (`ENSEMBLE_ENABLED=false`), runtime drops to ~2 minutes.
