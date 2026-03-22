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
- Uses Groq API (OpenAI-compatible) with Llama 3.3 70B
- Structured prompt engineering for probability estimation
- Returns: probability, confidence, reasoning, key_factors
- Rate limiting: 2.5s between requests (30 RPM Groq limit)
- Robust JSON parsing with regex fallbacks
- Automatic retry on parse failures (max 2 retries)
- Graceful fallback to market odds on total failure

### 4. Signal Generator (`signal_generator.py`)
- **Edge Formula**: `edge = llm_probability - market_odds`
- Five-tier classification: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
- **Score**: `abs(edge) * confidence` for ranking
- Exports to JSON with `latest.json` for dashboard consumption

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
```

API routes are simple `fs.readFile` operations that return JSON. The dashboard refreshes on page load - it's not real-time but sufficient for a signal generation system that runs periodically.

## Design Decisions

### Why Groq over OpenAI/Anthropic?
- Free tier with generous limits (30 RPM, 14400 RPD)
- Llama 3.3 70B provides strong reasoning at zero cost
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

The system's core hypothesis: **LLMs can detect information edges in prediction markets by synthesizing recent news faster than the market can price it in.**

```
Edge = P(LLM) - P(Market)

If Edge > threshold → the market hasn't fully priced in recent information
If Edge < -threshold → the market may be overpricing the event
```

The system is most valuable when:
1. News breaks that hasn't been reflected in market prices yet
2. The LLM can correctly interpret the impact of news on event probability
3. The confidence is high enough to filter noise from signal

## Rate Limits & Performance

| Component | Limit | Mitigation |
|-----------|-------|------------|
| Groq API | 30 RPM | 2.5s sleep between requests |
| Google RSS | None | Primary news source |
| NewsData.io | 200/day | Secondary, optional |
| Polymarket | None (public) | Basic httpx timeouts |

For 30 markets, the full pipeline takes approximately:
- Market fetch: ~2s
- News fetch: ~30s (parallel-capable, currently sequential)
- LLM analysis: ~75s (30 markets * 2.5s rate limit)
- Signal generation: <1s
- **Total: ~2 minutes**
