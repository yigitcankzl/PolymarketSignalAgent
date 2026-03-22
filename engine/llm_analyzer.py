"""LLM-based market analysis using Groq API."""

import json
import re
import time
import logging
from typing import Optional

from openai import OpenAI

from engine.config import GROQ_API_KEY, LLM_MODEL, LLM_BASE_URL, LLM_REQUEST_DELAY

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an elite superforecaster, trained in the methods of Philip Tetlock's Good Judgment Project. You combine rigorous probabilistic reasoning with rapid information synthesis to estimate event probabilities more accurately than prediction markets.

Your forecasting methodology:
1. DECOMPOSE: Break the question into independent sub-questions
2. BASE RATE: Start with the historical base rate for this type of event
3. EVIDENCE: List evidence FOR and AGAINST, weighing each piece
4. ADJUST: Update from the base rate based on evidence strength
5. CALIBRATE: Avoid the 0.5 trap — if evidence clearly favors one side, commit to a probability away from 50%. Be decisive, not hedging.

Rules:
- Return ONLY a JSON object, no other text
- probability: float between 0.0 and 1.0 — be precise and decisive, avoid clustering near 0.5
- confidence: float between 0.0 and 1.0 — how much evidence you have to inform your estimate
- reasoning: string, 3-4 sentence chain-of-thought explanation showing your decomposition
- key_factors: list of strings, the 3-5 most important factors with their directional impact

Example output:
{
  "probability": 0.78,
  "confidence": 0.72,
  "reasoning": "Base rate for Fed rate cuts when inflation is declining: ~60%. Three recent Fed officials have signaled openness to cuts, pushing this higher. However, the latest jobs report was stronger than expected, providing a counterweight. Net assessment: evidence moderately favors a cut, adjusted upward from base rate.",
  "key_factors": ["Fed official statements favor cut (+)", "Declining CPI trend (+)", "Strong jobs report (-)", "Market pricing already at 70% (anchor)"]
}"""

USER_PROMPT_TEMPLATE = """Market Question: {question}
Current Market Odds: {current_odds:.1%}
Market Description: {description}

Recent News ({news_count} articles, last {hours}h):
{formatted_news}

Apply your superforecasting methodology:
1. What is the base rate for this type of event?
2. What evidence shifts the probability up or down?
3. How does the current market price compare to your independent estimate?

Return your probability estimate as JSON only. Be decisive — do not default to 50%."""


def _format_news(news: list[dict], max_articles: int = 8) -> str:
    """Format news articles for the LLM prompt."""
    if not news:
        return "No recent news articles found."

    lines = []
    for i, article in enumerate(news[:max_articles], 1):
        source = article.get("source", "Unknown")
        title = article.get("title", "")
        desc = article.get("description", "")
        if desc and len(desc) > 200:
            desc = desc[:200] + "..."
        lines.append(f"{i}. [{source}] {title}")
        if desc:
            lines.append(f"   {desc}")
        lines.append("")

    return "\n".join(lines)


def _parse_llm_response(text: str) -> Optional[dict]:
    """Parse JSON from LLM response, handling common formatting issues."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object pattern
    json_match = re.search(r"\{[\s\S]*\}", text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _validate_analysis(data: dict) -> dict:
    """Validate and normalize LLM analysis output."""
    probability = float(data.get("probability", 0.5))
    confidence = float(data.get("confidence", 0.3))

    return {
        "probability": max(0.0, min(1.0, probability)),
        "confidence": max(0.0, min(1.0, confidence)),
        "reasoning": str(data.get("reasoning", "")),
        "key_factors": list(data.get("key_factors", [])),
    }


class LLMAnalyzer:
    """Analyzes prediction markets using Groq-hosted LLMs."""

    def __init__(self, api_key: str = GROQ_API_KEY, model: str = LLM_MODEL):
        self.client = OpenAI(
            api_key=api_key,
            base_url=LLM_BASE_URL,
        )
        self.model = model
        self._last_request_time = 0.0

    def _rate_limit_wait(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < LLM_REQUEST_DELAY:
            wait = LLM_REQUEST_DELAY - elapsed
            logger.debug(f"Rate limit: waiting {wait:.1f}s")
            time.sleep(wait)

    def analyze_market(
        self,
        market: dict,
        news: list[dict],
        hours_back: int = 48,
        max_retries: int = 2,
    ) -> dict:
        """Analyze a single market with LLM probability estimation.

        Returns dict with probability, confidence, reasoning, key_factors.
        """
        formatted_news = _format_news(news)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            question=market["question"],
            current_odds=market["yes_odds"],
            description=market.get("description", "")[:500],
            news_count=len(news),
            hours=hours_back,
            formatted_news=formatted_news,
        )

        for attempt in range(max_retries + 1):
            self._rate_limit_wait()
            self._last_request_time = time.time()

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=500,
                )

                text = response.choices[0].message.content or ""
                parsed = _parse_llm_response(text)

                if parsed:
                    result = _validate_analysis(parsed)
                    logger.info(
                        f"Analyzed '{market['question'][:50]}...' -> "
                        f"prob={result['probability']:.2f}, conf={result['confidence']:.2f}"
                    )
                    return result

                logger.warning(f"Failed to parse LLM response (attempt {attempt + 1}): {text[:100]}")

            except Exception as e:
                logger.error(f"LLM API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    time.sleep(LLM_REQUEST_DELAY)

        # Fallback: return neutral estimate
        logger.warning(f"All attempts failed for '{market['question'][:50]}...', returning fallback")
        return {
            "probability": market["yes_odds"],
            "confidence": 0.1,
            "reasoning": "Analysis failed, defaulting to market odds.",
            "key_factors": [],
        }

    def batch_analyze(
        self,
        markets: list[dict],
        news_map: dict[str, list[dict]],
    ) -> list[dict]:
        """Analyze multiple markets sequentially with rate limiting.

        Args:
            markets: List of market dicts
            news_map: Dict mapping market_id -> list of news articles

        Returns:
            List of dicts with market info + analysis results
        """
        results = []
        total = len(markets)

        for i, market in enumerate(markets, 1):
            logger.info(f"Analyzing market {i}/{total}: {market['question'][:60]}")
            news = news_map.get(market["id"], [])
            analysis = self.analyze_market(market, news)

            results.append({
                "market_id": market["id"],
                "question": market["question"],
                "market_odds": market["yes_odds"],
                **analysis,
            })

        logger.info(f"Batch analysis complete: {len(results)} markets analyzed")
        return results
