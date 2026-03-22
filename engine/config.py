"""Configuration and constants for the signal engine."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
MARKETS_DIR = DATA_DIR / "markets"
SIGNALS_DIR = DATA_DIR / "signals"
NEWS_DIR = DATA_DIR / "news"
BACKTEST_DIR = DATA_DIR / "backtest"

# Synthesis API (unified Polymarket + Kalshi)
SYNTHESIS_API_KEY = os.getenv("SYNTHESIS_API_KEY", "")
SYNTHESIS_SECRET_KEY = os.getenv("SYNTHESIS_SECRET_KEY", "")
SYNTHESIS_BASE_URL = "https://synthesis.trade"

# Polymarket API (fallback if Synthesis unavailable)
POLYMARKET_API_URL = os.getenv("POLYMARKET_API_URL", "https://gamma-api.polymarket.com")

# Groq LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_BASE_URL = "https://api.groq.com/openai/v1"
LLM_REQUEST_DELAY = 2.5  # seconds between requests (30 RPM limit)

# Ensemble models (multiple models for consensus)
ENSEMBLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "qwen/qwen3-32b",
]
ENSEMBLE_ENABLED = os.getenv("ENSEMBLE_ENABLED", "true").lower() == "true"

# News
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_HOURS_BACK = int(os.getenv("NEWS_HOURS_BACK", "48"))
NEWS_MAX_RESULTS = 10

# Signal thresholds
SIGNAL_EDGE_THRESHOLD = float(os.getenv("SIGNAL_EDGE_THRESHOLD", "0.05"))
SIGNAL_CONFIDENCE_THRESHOLD = float(os.getenv("SIGNAL_CONFIDENCE_THRESHOLD", "0.4"))
STRONG_SIGNAL_EDGE = 0.10
STRONG_SIGNAL_CONFIDENCE = 0.5

# Pipeline
MAX_MARKETS = int(os.getenv("MAX_MARKETS", "30"))
MIN_VOLUME = 10000  # minimum market volume to consider
