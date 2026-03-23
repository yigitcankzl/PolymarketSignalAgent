<div align="center">

# Polymarket Signal Agent

### AI-Powered Prediction Market Trading System

[![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js_14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Tailwind](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Groq](https://img.shields.io/badge/Groq_AI-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![Synthesis](https://img.shields.io/badge/Synthesis.trade-8B5CF6?style=for-the-badge&logoColor=white)](https://synthesis.trade)
[![Framer Motion](https://img.shields.io/badge/Framer_Motion-0055FF?style=for-the-badge&logo=framer&logoColor=white)](https://www.framer.com/motion)
[![Recharts](https://img.shields.io/badge/Recharts-22C55E?style=for-the-badge&logo=chart.js&logoColor=white)](https://recharts.org)

**Orderflow 001 Hackathon** — AI-Augmented Systems Track | **Sponsor:** [Synthesis.trade](https://synthesis.trade)

</div>
>
> An end-to-end AI trading system for prediction markets. Fetches live data from Polymarket and Kalshi via [Synthesis.trade](https://synthesis.trade) unified API, analyzes with a multi-LLM ensemble, detects cross-platform arbitrage, and executes trades — all from a single dashboard.

## Demo

**Video:** [Watch Demo](#) *(2-3 min)*

**Live Output (Real Data):**
```
[STRONG_BUY] Utah State vs. Arizona Wildcats
  Market: 14.0% | AI: 67.6% | Edge: +53.6% | Kelly: 5.0%

[STRONG_BUY] Colorado Avalanche — NHL Stanley Cup
  Market: 20.5% | AI: 57.5% | Edge: +37.0% | Kelly: 5.0%

[STRONG_SELL] US forces enter Iran by March 31?
  Market: 20.9% | AI: 4.8% | Edge: -16.1% | Kelly: 5.0%

Cross-Platform Arbitrage:
  Buffalo Sabres: Polymarket 5.8% vs Kalshi 10.0% → +4.2% spread
  Luka Doncic MVP: Polymarket 8.3% vs Kalshi 12.0% → +3.7% spread

--- 9 signals | 8 arbitrage opportunities | 110s pipeline ---
```
All from **live API calls** — zero mock data in the signal pipeline.

## Strategy Logic

### Edge Hypothesis
LLM ensembles can detect information edges in prediction markets by synthesizing news faster than the crowd can price it in. When the AI's calibrated probability estimate diverges significantly from market odds, a tradeable edge exists.

### How We Find Edge
```
1. FETCH    → Live market odds from Polymarket + Kalshi (via Synthesis.trade)
2. RESEARCH → Google News RSS: real-time news per market
3. ANALYZE  → 3-model LLM ensemble estimates true probability
4. CALIBRATE → Platt scaling fixes LLM hedging bias (0.6→0.65, 0.7→0.78)
5. COMPARE  → Edge = AI_Probability − Market_Odds
6. SIZE     → Kelly criterion determines position size (quarter Kelly, 5% cap)
7. SIGNAL   → STRONG_BUY/SELL if edge > 10% with > 50% confidence
```

### Risk Management
- **Kelly criterion**: Optimal position sizing — never risking more than the edge justifies
- **Quarter Kelly**: 0.25× full Kelly for safety margin against estimation errors
- **5% cap**: Maximum allocation per market prevents catastrophic single-market loss
- **Confidence weighting**: Low-confidence signals get smaller positions automatically
- **Ensemble spread**: When models disagree, confidence drops → position shrinks

### Cross-Platform Arbitrage
Same outcome priced differently on Polymarket vs Kalshi = risk-free profit. We scan **1,400+ outcomes** across both platforms, match by name, verify same event via title similarity, and flag price discrepancies > 2%.

### Signal Classification

| Signal | Condition | Action |
|--------|-----------|--------|
| **STRONG_BUY** | Edge > +10%, Confidence > 50% | Buy YES shares |
| **BUY** | Edge > +5%, Confidence > 40% | Buy YES shares |
| **HOLD** | Edge within thresholds | No action |
| **SELL** | Edge < -5%, Confidence > 40% | Buy NO shares |
| **STRONG_SELL** | Edge < -10%, Confidence > 50% | Buy NO shares |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    POLYMARKET SIGNAL AGENT                               │
│                                                                         │
│  ┌──────────────────┐                                                   │
│  │  Synthesis.trade  │ ← Unified API: Polymarket (Polygon) + Kalshi     │
│  │  API Client       │   Markets, prices, wallets, orders               │
│  └────────┬──────────┘                                                  │
│           │                                                             │
│  ┌────────▼──────────┐   ┌──────────────┐   ┌────────────────────────┐ │
│  │  News Fetcher     │──→│ LLM Ensemble │──→│  Platt Scaling         │ │
│  │  Google News RSS  │   │ Llama 3.3 70B│   │  Calibration           │ │
│  │  per-market       │   │ Llama 3.1 8B │   │  α=1.5                 │ │
│  └───────────────────┘   │ Qwen3 32B    │   └──────────┬─────────────┘ │
│                          │ Median Agg.  │              │               │
│                          └──────────────┘              │               │
│                                                        ▼               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Signal Generator: Edge + Kelly Sizing + 5-tier classification  │   │
│  └──────────────────────────┬──────────────────────────────────────┘   │
│                              │                                         │
│  ┌───────────────┐  ┌───────▼───────┐  ┌────────────────────────────┐ │
│  │ Cross-Platform │  │   Trading     │  │  Dashboard (Next.js 14)    │ │
│  │ Arbitrage      │  │   Execution   │  │                            │ │
│  │ 1,400 outcomes │  │   Synthesis   │  │  Run Pipeline button       │ │
│  │ 8 verified arb │  │   Wallet API  │  │  One-click BUY/SELL        │ │
│  │ 2-4% spreads   │  │   Order API   │  │  Live pipeline progress    │ │
│  └───────────────┘  └───────────────┘  │  Arbitrage panel           │ │
│                                         │  Auto-refresh 30s          │ │
│                                         └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### File Structure
```
polymarket-signal-agent/
├── engine/                        # Python signal engine (14 modules)
│   ├── synthesis_client.py        # Synthesis.trade unified API
│   ├── trader.py                  # Account, wallet, order execution
│   ├── llm_analyzer.py            # 3-model ensemble + Platt calibration
│   ├── signal_generator.py        # Edge + Kelly + signal classification
│   ├── arbitrage.py               # Cross-platform arb detection
│   ├── news_fetcher.py            # Google News RSS + caching
│   ├── backtester.py              # PnL, Sharpe, hit rate metrics
│   ├── polymarket_client.py       # Direct Polymarket API (fallback)
│   ├── kalshi_client.py           # Direct Kalshi API
│   ├── price_history.py           # CLOB price history
│   ├── data_store.py              # JSON persistence
│   ├── config.py                  # Configuration
│   └── main.py                    # 7-step pipeline with status reporting
├── dashboard/                     # Next.js 14 trading terminal
│   └── src/
│       ├── app/api/               # 10 API routes
│       │   ├── run-pipeline/      # Trigger pipeline from UI
│       │   ├── pipeline-status/   # Real-time step progress
│       │   ├── trade/             # Place orders via Synthesis
│       │   ├── signals/           # Signal data
│       │   ├── arbitrage/         # Arbitrage data
│       │   ├── trading/           # Wallet/positions/PnL
│       │   └── ...
│       └── components/            # 13 UI components
│           ├── signal-table.tsx   # Signals + BUY/SELL buttons
│           ├── pipeline-status.tsx # Live execution progress
│           ├── arbitrage-panel.tsx # Cross-platform opportunities
│           ├── trading-panel.tsx  # Wallet balance/positions
│           └── ...
├── data/                          # Live pipeline output (JSON)
└── scripts/                       # Utilities
```

## Data Sources

| Source | Data | Auth | Status |
|--------|------|------|--------|
| [Synthesis.trade](https://synthesis.trade) | Polymarket + Kalshi markets, wallet, orders | API Key | **Live** |
| [Groq](https://console.groq.com) | LLM ensemble (3 models) | API Key | **Live** |
| Google News RSS | Real-time news per market | None | **Live** |

## Performance Metrics

### Live Signal Output (March 22, 2026)
| Metric | Value |
|--------|-------|
| Markets analyzed | 10 |
| Actionable signals | 9/10 (90%) |
| Cross-platform arb opportunities | 8 |
| Avg edge (absolute) | 24.6% |
| Pipeline runtime | 110s |
| LLM models in ensemble | 3 |
| Outcomes scanned for arb | 1,373 |

### Edge Calculation
```
Raw Probability  = median(Llama70B, Llama8B, Qwen32B)
Calibrated P     = 1 / (1 + exp(-1.5 × logit(Raw_P)))
Edge             = Calibrated_P − Market_Odds
Kelly Fraction   = (p×b − q) / b × 0.25, capped at 5%
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Market Data** | [Synthesis.trade API](https://synthesis.trade) — unified Polymarket + Kalshi |
| **AI/ML** | [Groq](https://console.groq.com) — Llama 3.3 70B + Llama 3.1 8B + Qwen3 32B |
| **Engine** | Python 3.11+, httpx, feedparser, openai SDK |
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Recharts, Framer Motion |
| **Trading** | Synthesis.trade Wallet + Order API (Polygon chain) |

## Setup & Run

### Prerequisites
- Python 3.11+, Node.js 18+
- [Groq API key](https://console.groq.com) (free)
- [Synthesis.trade API key](https://synthesis.trade) (free)

### Quick Start
```bash
git clone <repo-url>
cd polymarket-signal-agent

# Engine
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Dashboard
cd dashboard && npm install && cd ..

# Configure
cp .env.example .env
# Add: GROQ_API_KEY, SYNTHESIS_API_KEY, SYNTHESIS_SECRET_KEY

# Run
cd dashboard && npm run dev
# Open http://localhost:3000 → click "Run Pipeline"
```

### CLI
```bash
python3 -m engine.main --markets 10           # Signals + arbitrage
python3 -m engine.main --markets 10 --trade   # + auto-execute orders
python3 -m engine.main --markets 10 -v        # Verbose logging
```

## Key Features

### Signal Engine
- **Multi-LLM Ensemble** — 3 models with median aggregation for robust probability estimates
- **Superforecaster Prompting** — Tetlock methodology: base rate → evidence → adjustment → decisive estimate
- **Platt Scaling** — Fixes systematic LLM hedging bias toward 0.5
- **Kelly Criterion** — Risk-adjusted position sizing (quarter Kelly, 5% cap)

### Cross-Platform Arbitrage
- Scans **1,400+ outcomes** across Polymarket and Kalshi via Synthesis.trade
- Outcome-name matching with event verification (filters false positives)
- **8 verified arbitrage opportunities** found per run (2-4% spreads)
- Direct [Synthesis.trade](https://synthesis.trade) links for execution

### Trading Execution
- Automated account + wallet setup via Synthesis API
- One-click BUY/SELL from dashboard with Kelly-sized amounts
- Live wallet balance, positions, PnL tracking
- Polygon wallet: `0xdD92F2278C4242750E0959Db120710BeF9a0eCDC`

### Dashboard
- **Run Pipeline** — Green button triggers full pipeline from the UI
- **Live Progress** — Step-by-step animation: markets → news → AI → signals → arbitrage
- **One-Click Trading** — BUY/SELL buttons on each signal
- **Arbitrage Panel** — Cross-platform price comparisons with Synthesis.trade links
- **Auto-Refresh** — 30s polling, toast notifications, animated counters
- **Mobile Responsive** — Card layout on small screens

## Sponsor Integration — Synthesis.trade

This project is built entirely on [Synthesis.trade](https://synthesis.trade):

| Integration | How |
|-------------|-----|
| **Market Data** | All Polymarket + Kalshi data via Synthesis unified API |
| **Arbitrage** | Cross-platform outcome matching using Synthesis endpoints |
| **Trading** | Account, wallet, order execution via Synthesis API |
| **Dashboard** | Every signal and arb opportunity links to Synthesis.trade |
| **Branding** | Header "via Synthesis.trade", footer "Powered by Synthesis.trade" |

## What's Real vs Simulated

| Component | Status |
|-----------|--------|
| Market prices | **Live** — Synthesis.trade API |
| News | **Live** — Google News RSS |
| LLM analysis | **Live** — Groq API (3-model ensemble) |
| Signals | **Live** — computed from live data |
| Arbitrage | **Live** — 1,400+ outcomes matched |
| Trading wallet | **Live** — Synthesis API |
| Backtest | Simulated (no resolved markets yet) |

---

Built solo for [Orderflow 001](https://ordeflow-001.devpost.com) Hackathon, March 22-24, 2026.
