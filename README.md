# Polymarket Signal Agent

AI-powered signal system that analyzes Polymarket prediction markets, evaluates news sources with LLM (Groq - Llama 3.3 70B), and generates trading signals by detecting edge between AI probability estimates and market odds.

**Track:** AI-Augmented Systems

## What It Does

Prediction markets aggregate crowd wisdom into prices, but information asymmetry creates opportunities. This agent:

1. **Fetches** active markets from Polymarket's CLOB API
2. **Gathers** relevant news from Google News RSS and other sources
3. **Analyzes** each market with an LLM to estimate event probability
4. **Calculates edge** (LLM estimate vs market odds) and generates signals
5. **Backtests** signal accuracy against resolved markets
6. **Visualizes** everything in a real-time dashboard

## How It Works

```
Polymarket API ──→ Active Markets ──→ News Fetcher ──→ LLM Analyzer ──→ Signal Generator
                                         │                  │                  │
                                    Google RSS        Groq (Llama 3.3)    Edge Calculation
                                    NewsData.io       70B Versatile       STRONG_BUY/SELL
                                         │                  │                  │
                                         └──────────────────┴──────────────────┘
                                                          │
                                                    ┌─────┴─────┐
                                                    │ Backtester │
                                                    │ Dashboard  │
                                                    └───────────┘
```

### Signal Classification

| Signal | Condition |
|--------|-----------|
| **STRONG_BUY** | Edge > +10% and Confidence > 50% |
| **BUY** | Edge > +5% and Confidence > 40% |
| **HOLD** | Edge within thresholds |
| **SELL** | Edge < -5% and Confidence > 40% |
| **STRONG_SELL** | Edge < -10% and Confidence > 50% |

## Architecture

```
polymarket-signal-agent/
├── engine/                     # Python core engine
│   ├── config.py               # API keys, constants, thresholds
│   ├── polymarket_client.py    # Polymarket API client
│   ├── news_fetcher.py         # Multi-source news gathering
│   ├── llm_analyzer.py         # Groq LLM probability estimation
│   ├── signal_generator.py     # Edge calculation + signal generation
│   ├── backtester.py           # Backtest engine with metrics
│   ├── data_store.py           # JSON-based data persistence
│   └── main.py                 # CLI entry point
├── dashboard/                  # Next.js 14 frontend
│   └── src/
│       ├── app/                # Pages + API routes
│       └── components/         # Dashboard UI components
├── data/                       # Pipeline output (JSON)
└── scripts/
    ├── seed_data.py            # Demo data generator
    └── run_pipeline.sh         # Pipeline runner script
```

## Tech Stack

### Engine
- **Python 3.11+** with type hints
- **Groq API** (Llama 3.3 70B Versatile) - probability estimation
- **Polymarket Gamma API** - market data
- **feedparser** - Google News RSS parsing
- **pandas** - data processing
- **httpx** - async-capable HTTP client

### Dashboard
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS** - dark theme
- **Recharts** - PnL and edge charts
- **Lucide React** - icons

## Performance Metrics

From backtesting against resolved markets:

| Metric | Value |
|--------|-------|
| Hit Rate | 61.1% |
| Total P&L | +2.053 |
| Sharpe Ratio | Positive |
| Profit Factor | > 1.0 |
| Actionable Signals | 23/25 |

## Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Clone & Install

```bash
git clone https://github.com/your-repo/polymarket-signal-agent.git
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
# Full pipeline (requires GROQ_API_KEY)
python -m engine.main --markets 20 --backtest

# With all options
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

- **Stats Overview** - Hit rate, Sharpe ratio, total signals, average edge
- **Signal Table** - All signals ranked by score with color-coded badges
- **P&L Chart** - Cumulative profit/loss curve
- **Edge Distribution** - Bar chart of edge values across markets
- **Backtest Panel** - Detailed performance metrics
- **Signal Breakdown** - Distribution of signal types
- **Top Signals** - Highest-conviction picks with reasoning

## Future Work

- Live trading integration with Polymarket order placement
- Multi-model ensemble (GPT-4, Claude, Llama) for consensus estimates
- Real-time WebSocket updates for market odds
- Additional data sources (Twitter/X sentiment, on-chain data)
- Portfolio optimization with Kelly criterion sizing
- Alert system (email/Telegram) for high-conviction signals
