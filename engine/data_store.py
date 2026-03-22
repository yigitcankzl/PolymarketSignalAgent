"""Simple JSON-based local data storage."""

import json
import logging
from pathlib import Path
from typing import Optional

from engine.config import DATA_DIR, SIGNALS_DIR, MARKETS_DIR, BACKTEST_DIR

logger = logging.getLogger(__name__)


def load_json(filepath: Path) -> Optional[dict | list]:
    """Load a JSON file, returning None if it doesn't exist."""
    if not filepath.exists():
        return None
    try:
        return json.loads(filepath.read_text())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse {filepath}: {e}")
        return None


def save_json(filepath: Path, data: dict | list) -> None:
    """Save data as JSON to a file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(json.dumps(data, indent=2, default=str))


def load_latest_signals() -> Optional[dict]:
    """Load the most recent signals file."""
    return load_json(SIGNALS_DIR / "latest.json")


def load_latest_markets() -> Optional[dict]:
    """Load the most recent market snapshot."""
    return load_json(MARKETS_DIR / "latest.json")


def load_latest_backtest() -> Optional[dict]:
    """Load the most recent backtest results."""
    return load_json(BACKTEST_DIR / "latest.json")


def get_resolved_markets(markets_data: dict) -> dict[str, float]:
    """Extract resolved markets and their resolutions.

    Returns dict mapping market_id -> resolution (1.0 or 0.0)
    """
    resolutions = {}
    for market in markets_data.get("markets", []):
        if market.get("resolved") and market.get("resolution") is not None:
            try:
                res = float(market["resolution"])
                resolutions[market["id"]] = res
            except (ValueError, TypeError):
                pass
    return resolutions
