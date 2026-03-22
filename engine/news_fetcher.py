"""News fetcher for gathering relevant articles about prediction markets."""

import json
import hashlib
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import quote_plus

import httpx
import feedparser

from engine.config import NEWS_DIR, NEWS_API_KEY, NEWS_HOURS_BACK, NEWS_MAX_RESULTS

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "will", "the", "be", "is", "are", "was", "were", "been", "being",
    "have", "has", "had", "do", "does", "did", "a", "an", "and", "but",
    "if", "or", "as", "of", "at", "by", "for", "with", "to", "from",
    "in", "on", "it", "its", "this", "that", "what", "which", "who",
    "whom", "when", "where", "why", "how", "before", "after", "above",
    "below", "between", "under", "again", "then", "once", "there",
}


def extract_keywords(question: str) -> str:
    """Extract search keywords from a market question.

    Removes stop words and punctuation, keeping meaningful terms.
    """
    cleaned = re.sub(r"[^\w\s]", "", question)
    words = cleaned.split()
    keywords = [w for w in words if w.lower() not in STOP_WORDS and len(w) > 1]
    return " ".join(keywords[:8])


def _hash_title(title: str) -> str:
    """Create a hash for deduplication."""
    normalized = re.sub(r"\s+", " ", title.lower().strip())
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def fetch_google_rss(query: str, max_results: int = 10) -> list[dict]:
    """Fetch news from Google News RSS feed."""
    encoded = quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_results]:
            published = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()

            articles.append({
                "title": entry.get("title", ""),
                "description": entry.get("summary", ""),
                "source": entry.get("source", {}).get("title", "Google News"),
                "published_at": published,
                "url": entry.get("link", ""),
            })

        logger.info(f"Google RSS: {len(articles)} articles for '{query}'")
        return articles
    except Exception as e:
        logger.error(f"Google RSS fetch failed: {e}")
        return []


def fetch_newsdata(query: str, max_results: int = 5) -> list[dict]:
    """Fetch news from NewsData.io API (free tier)."""
    if not NEWS_API_KEY:
        return []

    try:
        resp = httpx.get(
            "https://newsdata.io/api/1/latest",
            params={"apikey": NEWS_API_KEY, "q": query, "language": "en"},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for item in (data.get("results") or [])[:max_results]:
            articles.append({
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "source": item.get("source_id", "NewsData"),
                "published_at": item.get("pubDate", ""),
                "url": item.get("link", ""),
            })

        logger.info(f"NewsData: {len(articles)} articles for '{query}'")
        return articles
    except Exception as e:
        logger.error(f"NewsData fetch failed: {e}")
        return []


def fetch_news(
    query: str,
    max_results: int = NEWS_MAX_RESULTS,
    hours_back: int = NEWS_HOURS_BACK,
) -> list[dict]:
    """Fetch news from multiple sources, deduplicated.

    Combines Google News RSS and optional NewsData.io results.
    """
    all_articles = []

    # Primary source: Google News RSS (no rate limits)
    all_articles.extend(fetch_google_rss(query, max_results))

    # Secondary source: NewsData.io (if API key available)
    all_articles.extend(fetch_newsdata(query, max_results=5))

    # Deduplicate by title hash
    seen: set[str] = set()
    unique: list[dict] = []
    for article in all_articles:
        h = _hash_title(article["title"])
        if h not in seen and article["title"]:
            seen.add(h)
            unique.append(article)

    # Filter by time window
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    filtered = []
    for article in unique:
        if article["published_at"]:
            try:
                pub = datetime.fromisoformat(article["published_at"].replace("Z", "+00:00"))
                if pub < cutoff:
                    continue
            except ValueError:
                pass
        filtered.append(article)

    result = filtered[:max_results]
    logger.info(f"Total: {len(result)} unique articles for '{query}' (last {hours_back}h)")
    return result


def cache_news(market_id: str, news: list[dict]) -> None:
    """Cache fetched news to avoid re-fetching."""
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = NEWS_DIR / f"{market_id}.json"
    filepath.write_text(json.dumps(news, indent=2, default=str))


def load_cached_news(market_id: str, max_age_hours: int = 6) -> Optional[list[dict]]:
    """Load cached news if fresh enough."""
    filepath = NEWS_DIR / f"{market_id}.json"
    if not filepath.exists():
        return None

    import os
    mtime = datetime.fromtimestamp(os.path.getmtime(filepath), tz=timezone.utc)
    if datetime.now(timezone.utc) - mtime > timedelta(hours=max_age_hours):
        return None

    try:
        return json.loads(filepath.read_text())
    except json.JSONDecodeError:
        return None


def fetch_news_for_market(market: dict, use_cache: bool = True) -> list[dict]:
    """Fetch news for a specific market, with caching support."""
    market_id = market["id"]

    if use_cache:
        cached = load_cached_news(market_id)
        if cached is not None:
            logger.info(f"Using cached news for market {market_id}")
            return cached

    query = extract_keywords(market["question"])
    news = fetch_news(query)

    cache_news(market_id, news)
    return news
