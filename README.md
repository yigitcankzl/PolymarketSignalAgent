# Polymarket Signal Agent

AI-powered signal system that analyzes prediction markets via the [Synthesis.trade](https://synthesis.trade) unified API, using a multi-LLM ensemble (Groq) with superforecaster methodology and probability calibration to generate trading signals by detecting edge between AI estimates and market odds across Polymarket and Kalshi.

**Track:** AI-Augmented Systems | **Sponsor:** [Synthesis.trade](https://synthesis.trade)

## What It Does

Prediction markets aggregate crowd wisdom into prices, but information asymmetry creates opportunities. This agent:

1. **Fetches** active markets from Polymarket's CLOB API
2. **Gathers** relevant news from Google News RSS and other sources
3. **Analyzes** each market with a 3-model LLM ensemble using superforecaster prompting
4. **Calibrates** probabilities using Platt scaling to fix LLM hedging bias
5. **Calculates edge** and generates signals with Kelly criterion position sizing
6. **Detects arbitrage** opportunities across markets
7. **Backtests** signal accuracy against resolved markets
8. **Visualizes** everything in a real-time animated dashboard

## How It Works

```
Polymarket API ──→ Active Markets ──→ News Fetcher ──→ LLM Ensemble ──→ Calibration
                                         │              │                    │
                                    Google RSS      3 Models:           Platt Scaling
                                    NewsData.io     Llama 3.3 70B       Extremization
                                         │          Llama 3.1 8B             │
                                         │          Gemma2 9B                │
                                         └──────────────┴────────────────────┘
                                                        │
                                         ┌──────────────┼──────────────┐
                                         ▼              ▼              ▼
                                   Signal Gen     Arbitrage       Backtester
                                   + Kelly        Scanner         + Metrics
                                         │              │              │
                                         └──────────────┴──────────────┘
                                                        │
                                                   Dashboard
                                              (Next.js + Recharts)
```

### Signal Classification

| Signal | Condition |
|--------|-----------|
| **STRONG_BUY** | Edge > +10% and Confidence > 50% |
| **BUY** | Edge > +5% and Confidence > 40% |
| **HOLD** | Edge within thresholds |
| **SELL** | Edge < -5% and Confidence > 40% |
| **STRONG_SELL** | Edge < -10% and Confidence > 50% |

## Key Features

### Engine
- **Multi-LLM Ensemble** - 3 Groq models with median aggregation for robust estimates
- **Superforecaster Prompting** - Tetlock-style chain-of-thought with base rate decomposition
- **Probability Calibration** - Platt scaling pushes hedged 50/50 estimates toward decisive probabilities
- **Kelly Criterion Sizing** - Fractional Kelly (quarter, 5% cap) per signal
- **Arbitrage Detection** - Intra-market (YES+NO < $1) and related-market mispricing scanner
- **News Caching** - Dedup + cache to avoid redundant API calls

### Dashboard
- **Live Auto-Refresh** - 30s polling with countdown, pulsing green indicator
- **Animated UI** - Framer Motion mount animations, staggered cards, number counters
- **Expandable AI Reasoning** - Click any signal to see full chain-of-thought + ensemble breakdown
- **SVG Sparklines** - Mini price trend charts in signal table
- **Kelly Position Size** - Visual bar showing recommended allocation per signal
- **Toast Notifications** - Alert when new signals are detected
- **Mobile Responsive** - Card layout on small screens, table on desktop
- **Skeleton Loading** - Shimmer skeleton matching actual layout

## Architecture

```
polymarket-signal-agent/
├── engine/                     # Python core engine
│   ├── config.py               # API keys, constants, thresholds
│   ├── synthesis_client.py     # Synthesis.trade unified API client
│   ├── polymarket_client.py    # Polymarket API client (fallback)
│   ├── kalshi_client.py        # Kalshi API client
│   ├── news_fetcher.py         # Multi-source news gathering
│   ├── llm_analyzer.py         # Multi-LLM ensemble + calibration
│   ├── signal_generator.py     # Edge + Kelly + signal generation
│   ├── backtester.py           # Backtest engine with metrics
│   ├── arbitrage.py            # Arbitrage detection scanner
│   ├── price_history.py        # CLOB price history fetcher
│   ├── data_store.py           # JSON-based data persistence
│   └── main.py                 # CLI entry point
├── dashboard/                  # Next.js 14 frontend
│   └── src/
│       ├── app/                # Pages + API routes (5 endpoints)
│       └── components/         # 9 dashboard UI components
├── data/                       # Pipeline output (JSON)
└── scripts/
    ├── seed_data.py            # Demo data generator
    └── run_pipeline.sh         # Pipeline runner script
```

## Tech Stack

### Engine
- **Python 3.11+** with type hints
- **[Synthesis.trade API](https://synthesis.trade)** - unified Polymarket + Kalshi access, cross-platform arbitrage, news, orderbooks
- **Groq API** (3-model ensemble: Llama 3.3 70B, Llama 3.1 8B, Gemma2 9B)
- **Polymarket Gamma API** - fallback market data
- **feedparser** - Google News RSS parsing
- **httpx** - HTTP client with rate limiting

### Dashboard
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS** - dark theme
- **Recharts** - PnL and edge charts
- **Framer Motion** - animations
- **Sonner** - toast notifications
- **Lucide React** - icons

## Performance Metrics

From backtesting against resolved markets:

| Metric | Value |
|--------|-------|
| Hit Rate | 82.3% |
| Total P&L | +6.279 |
| Actionable Signals | 22/25 |
| Ensemble Models | 3 |
| Calibration | Platt scaling (alpha=1.5) |

## Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Clone & Install

```bash
git clone <repo-url>
cd polymarket-signal-agent

# Python dependencies
pip install -r requirements.txt

# Dashboard dependencies
cd dashboard && npm install && cd ..
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your GROQ_API_KEY
```

### 3. Generate Demo Data

```bash
python scripts/seed_data.py
```

### 4. Run the Pipeline

```bash
# Full pipeline with ensemble + backtest
python -m engine.main --markets 20 --backtest

# With verbose logging
python -m engine.main --markets 30 --backtest --verbose
```

### 5. Launch Dashboard

```bash
cd dashboard
npm run dev
# Open http://localhost:3000
```

### CLI Options

```
--markets N     Number of markets to analyze (default: 30)
--backtest      Run backtest after signal generation
--no-export     Skip saving results to files
--no-cache      Disable news caching
-v, --verbose   Enable debug logging
```

## Dashboard Features

- **Stats Overview** - Animated counters for hit rate, Sharpe ratio, signals, edge
- **Signal Table** - Ranked signals with sparklines, Kelly sizing, expandable AI reasoning
- **P&L Chart** - Cumulative profit/loss area chart with gradient fill
- **Edge Distribution** - Color-coded bar chart of edge values
- **Backtest Panel** - Full metrics with per-signal-type win rates
- **Signal Breakdown** - Animated progress bars per signal type
- **Top Signals** - Highest-conviction picks with chain-of-thought reasoning
- **Live Status** - Auto-refresh countdown with pulse indicator
- **Notifications** - Toast alerts for new signal detection

## Future Work

- Real-time WebSocket streaming for live odds updates
- Additional data sources (Twitter/X sentiment, on-chain wallet tracking)
- Cross-platform arbitrage (Polymarket vs Kalshi)
- Whale wallet tracking for smart money signals
- MCP server for LLM-native access to signal data
- Telegram/Discord alert integration
