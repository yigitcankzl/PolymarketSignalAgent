# Polymarket Signal Agent

An end-to-end AI trading system for prediction markets. Uses the [Synthesis.trade](https://synthesis.trade) unified API to fetch live data from both Polymarket and Kalshi, analyzes markets with a multi-LLM ensemble via Groq, detects cross-platform arbitrage, and executes trades — all from a single pipeline.

**Track:** AI-Augmented Systems | **Sponsor:** [Synthesis.trade](https://synthesis.trade)

## What It Does

Prediction markets aggregate crowd wisdom into prices, but information asymmetry creates exploitable edges. This system:

1. **Fetches** live markets from Polymarket + Kalshi via Synthesis.trade unified API
2. **Gathers** real-time news from Google News RSS per market
3. **Analyzes** each market with a 3-model LLM ensemble using superforecaster prompting
4. **Calibrates** probabilities using Platt scaling to fix LLM hedging bias
5. **Generates signals** with Kelly criterion position sizing
6. **Detects cross-platform arbitrage** by matching 1,400+ outcomes across Polymarket and Kalshi
7. **Executes trades** via Synthesis.trade wallet and order API
8. **Visualizes** everything in a real-time animated dashboard

## Live Output (Real Data, Not Mock)

```
================================================================================
SIGNAL SUMMARY — March 22, 2026
================================================================================

[STRONG_BUY] Utah State Aggies vs. Arizona Wildcats
  Market: 14.0% | LLM: 67.6% | Edge: +53.6% | Kelly: 5.0%

[STRONG_BUY] Colorado Avalanche — 2026 NHL Stanley Cup
  Market: 20.5% | LLM: 57.5% | Edge: +37.0% | Kelly: 5.0%

[STRONG_SELL] US forces enter Iran by March 31?
  Market: 20.9% | LLM: 4.8% | Edge: -16.1% | Kelly: 5.0%

[STRONG_BUY] UCLA Bruins vs. Connecticut Huskies
  Market: 34.9% | LLM: 63.3% | Edge: +27.4% | Kelly: 5.0%

--- 9 actionable signals | 8 cross-platform arbitrage opportunities ---
```

All data above is from **live API calls** — Synthesis.trade for market prices, Groq for LLM analysis, Google News for context. No mock data in the signal pipeline.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    POLYMARKET SIGNAL AGENT PIPELINE                      │
│                                                                         │
│  ┌──────────────────┐                                                   │
│  │  Synthesis.trade  │ ← Unified API for Polymarket + Kalshi            │
│  │  API Client       │   GET /api/v1/polymarket/markets                 │
│  │                   │   GET /api/v1/kalshi/markets                     │
│  └────────┬──────────┘                                                  │
│           │                                                             │
│  ┌────────▼──────────┐   ┌──────────────┐   ┌────────────────────────┐ │
│  │  News Fetcher     │──→│ LLM Ensemble │──→│  Probability           │ │
│  │  Google News RSS  │   │              │   │  Calibration           │ │
│  │  per-market       │   │ Llama 3.3 70B│   │                        │ │
│  │  keyword search   │   │ Llama 3.1 8B │   │  Platt Scaling         │ │
│  └───────────────────┘   │ Qwen3 32B    │   │  α=1.5 extremization  │ │
│                          │              │   │  0.6 → 0.65            │ │
│                          │ Median       │   │  0.7 → 0.78            │ │
│                          │ Aggregation  │   └──────────┬─────────────┘ │
│                          └──────────────┘              │               │
│                                                        │               │
│  ┌─────────────────────────────────────────────────────▼─────────────┐ │
│  │                    SIGNAL GENERATOR                                │ │
│  │  Edge = Calibrated_P − Market_Odds                                │ │
│  │  Signal = STRONG_BUY / BUY / HOLD / SELL / STRONG_SELL            │ │
│  │  Kelly = (edge × confidence) / odds × 0.25, capped at 5%         │ │
│  └──────────────────────────┬────────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────┐  ┌───────▼───────┐  ┌────────────────────────────┐ │
│  │ Cross-Platform │  │   Trade       │  │  Dashboard (Next.js)       │ │
│  │ Arbitrage      │  │   Execution   │  │  Real-time signals         │ │
│  │                │  │               │  │  Arbitrage panel           │ │
│  │ 664 PM outcomes│  │  Synthesis    │  │  Trading status            │ │
│  │ 709 KA outcomes│  │  Wallet API   │  │  PnL charts                │ │
│  │ 8 verified     │  │  Order API    │  │  Auto-refresh 30s          │ │
│  │ opportunities  │  │               │  │                            │ │
│  └───────────────┘  └───────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Signal Classification

| Signal | Condition | Action |
|--------|-----------|--------|
| **STRONG_BUY** | Edge > +10%, Confidence > 50% | Buy YES shares |
| **BUY** | Edge > +5%, Confidence > 40% | Buy YES shares |
| **HOLD** | Edge within thresholds | No action |
| **SELL** | Edge < -5%, Confidence > 40% | Buy NO shares |
| **STRONG_SELL** | Edge < -10%, Confidence > 50% | Buy NO shares |

## Key Features

### Signal Engine
- **Synthesis.trade Integration** — Single API for both Polymarket and Kalshi market data, wallet management, and order execution
- **Multi-LLM Ensemble** — 3 Groq models (Llama 3.3 70B, Llama 3.1 8B, Qwen3 32B) with median aggregation
- **Superforecaster Prompting** — Tetlock-style chain-of-thought: base rate → evidence for/against → adjustment → decisive probability
- **Platt Scaling Calibration** — Fixes LLM hedging bias by extremizing probabilities away from 0.5
- **Kelly Criterion Sizing** — Fractional Kelly (quarter Kelly, 5% cap) position sizing per signal

### Cross-Platform Arbitrage
- Scans **664 Polymarket + 709 Kalshi outcomes** per run
- Matches outcomes by name across platforms (e.g., "Buffalo Sabres" on both)
- Verifies same event via normalized title similarity (filters false positives)
- Found **8 verified arbitrage opportunities** in latest run (2-4% spreads)
- Direct [Synthesis.trade](https://synthesis.trade) links for one-click execution

### Automated Trading
- Account creation + API key management via Synthesis API
- Polygon wallet with deposit address (`0xdD92...eCDC`)
- Market order execution based on Kelly-sized signals
- Position tracking, PnL, and order history
- Persistent state across pipeline runs

### Dashboard (Full Trading Terminal)
- **Run Pipeline from UI** — Green "Run Pipeline" button triggers full signal generation from the dashboard
- **Live Step-by-Step Progress** — Real-time pipeline status: fetching markets → news → LLM analysis → signals → arbitrage → complete
- **One-Click Trading** — BUY/SELL buttons on each signal with Kelly-sized amounts, executes via Synthesis API
- **Expandable AI Reasoning** — Click any signal for full chain-of-thought + ensemble model breakdown
- **Cross-Platform Arbitrage Panel** — Price comparison cards with "Trade on Synthesis" buttons
- **Live Trading Panel** — Wallet balance, positions, orders from Synthesis API
- **Auto-Refresh** — 30s polling with countdown, toast notifications for new signals
- **Animated UI** — Framer Motion mount animations, number counters, skeleton loading
- **Mobile Responsive** — Card layout on small screens

## Architecture

```
polymarket-signal-agent/
├── engine/                        # Python signal engine
│   ├── synthesis_client.py        # Synthesis.trade unified API client
│   ├── trader.py                  # Automated trading (account, wallet, orders)
│   ├── llm_analyzer.py            # Multi-LLM ensemble + Platt calibration
│   ├── signal_generator.py        # Edge calculation + Kelly sizing
│   ├── arbitrage.py               # Cross-platform arbitrage detection
│   ├── news_fetcher.py            # Google News RSS with caching
│   ├── backtester.py              # PnL, Sharpe, hit rate metrics
│   ├── polymarket_client.py       # Direct Polymarket API (fallback)
│   ├── kalshi_client.py           # Direct Kalshi API
│   ├── price_history.py           # CLOB price history
│   ├── data_store.py              # JSON persistence
│   ├── config.py                  # Configuration + thresholds
│   └── main.py                    # 6-step CLI pipeline
├── dashboard/                     # Next.js 14 frontend
│   └── src/
│       ├── app/
│       │   ├── page.tsx           # Main dashboard page
│       │   └── api/               # 10 API routes (signals, markets, backtest,
│       │       └── ...            #   arbitrage, synthesis, trading, run-pipeline,
│       │                          #   pipeline-status, trade)
│       └── components/            # 13 UI components
│           ├── signal-table.tsx   # Signals with sparklines + BUY/SELL buttons
│           ├── arbitrage-panel.tsx # Cross-platform arb opportunities
│           ├── trading-panel.tsx  # Live wallet/positions/orders
│           ├── pipeline-status.tsx # Real-time pipeline execution progress
│           ├── pnl-chart.tsx      # Cumulative P&L area chart
│           └── ...
├── data/                          # Pipeline output (live JSON)
│   ├── signals/latest.json        # Current signals (from live API)
│   ├── arbitrage/latest.json      # Arbitrage opportunities (from live API)
│   ├── markets/latest.json        # Market snapshots (from live API)
│   ├── trader/state.json          # Trading account state
│   └── backtest/latest.json       # Backtest results
└── scripts/
    ├── seed_data.py               # Backtest seed data only
    └── run_pipeline.sh            # Pipeline runner
```

## Data Sources (All Live)

| Source | What | Auth |
|--------|------|------|
| **Synthesis.trade API** | Polymarket + Kalshi markets, prices, wallet, orders | API Key |
| **Groq API** | LLM probability estimation (3-model ensemble) | API Key |
| **Google News RSS** | Real-time news per market | None |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Data** | [Synthesis.trade API](https://synthesis.trade) (Polymarket + Kalshi unified) |
| **AI** | Groq (Llama 3.3 70B + Llama 3.1 8B + Qwen3 32B ensemble) |
| **Engine** | Python 3.11+, httpx, feedparser, pandas |
| **Dashboard** | Next.js 14, TypeScript, Tailwind, Recharts, Framer Motion |
| **Trading** | Synthesis.trade Wallet + Order API (Polygon chain) |

## Setup & Run

### Prerequisites
- Python 3.11+, Node.js 18+
- [Groq API key](https://console.groq.com) (free)
- [Synthesis.trade API key](https://synthesis.trade) (free)

### Install

```bash
git clone <repo-url>
cd polymarket-signal-agent

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cd dashboard && npm install && cd ..
```

### Configure

```bash
cp .env.example .env
# Add: GROQ_API_KEY, SYNTHESIS_API_KEY, SYNTHESIS_SECRET_KEY
```

### Run

```bash
# Launch dashboard (includes "Run Pipeline" button)
cd dashboard && npm run dev
# Open http://localhost:3000 → click green "Run Pipeline" button

# Or run from CLI:
python3 -m engine.main --markets 10

# With automated trading
python3 -m engine.main --markets 10 --trade
```

### CLI Options

```
--markets N     Number of markets to analyze (default: 30)
--backtest      Run backtest after signal generation
--trade         Execute top signals via Synthesis wallet
--no-cache      Re-fetch all news (ignore cache)
-v, --verbose   Debug logging
```

## Edge Calculation

```
Raw Probability  = median(Llama70B, Llama8B, Qwen32B)
Calibrated P     = 1 / (1 + exp(-1.5 × logit(Raw_P)))
Edge             = Calibrated_P − Market_Odds
Kelly Fraction   = (p×b − q) / b × 0.25, capped at 5%
Signal           = STRONG_BUY if edge > 10% and confidence > 50%
```

## Sponsor Integration

This project is built on [Synthesis.trade](https://synthesis.trade) — the unified prediction market API:

- **Market Data**: All Polymarket + Kalshi data flows through Synthesis API
- **Cross-Platform Arbitrage**: Matching outcomes across 1,400+ markets on both platforms
- **Trading Execution**: Account, wallet, and order management via Synthesis
- **Dashboard Links**: Every signal and arbitrage opportunity links directly to Synthesis.trade

Built for [Orderflow 001](https://ordeflow-001.devpost.com) Hackathon, March 2026.
