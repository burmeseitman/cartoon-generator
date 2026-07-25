"""Analyzes news articles from a comedian's viewpoint."""
import json
import logging
import os
from typing import Any, Dict, Optional

from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

COMEDY_ANALYSIS_PROMPT = """\
You are a stand-up comedian analyzing a news article for a funny cartoon.

Given the following news article, provide:
1. A COMEDIAN_ANGLE: One or two sentences capturing the humorous angle of this story
2. A CARTOON_PROMPT: A detailed English prompt for generating a funny cartoon/illustration 
   image. The prompt should describe a visual scene that satirizes or makes fun of the news.
   Include style direction (e.g., "in the style of a satirical editorial cartoon", 
   "funny webcomic style", "caricature illustration").
3. A ONE_LINER: A short punchy one-liner joke about this news (max 20 words)

Rules:
- Keep it light-hearted and witty, not offensive
- Focus on the absurdity or irony in the news
- The cartoon prompt must be visually descriptive enough to generate an image
- Do NOT include any real person's name in the cartoon prompt; use generic descriptors instead

Format your response as JSON with keys: comedian_angle, cartoon_prompt, one_liner

News Article:
Title: {title}
Description: {description}
URL: {url}
"""


def analyze_with_openai(title: str, description: str, url: str) -> Optional[Dict[str, Any]]:
    """Use OpenAI to get a comedian's analysis of the news article.

    Returns a dict with comedian_angle, cartoon_prompt, one_liner.
    Returns None if API is unavailable or fails.
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set; using fallback comedy analysis.")
        return None

    try:
        import openai

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        prompt = COMEDY_ANALYSIS_PROMPT.format(title=title, description=description, url=url)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=1.2,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()
        # Try to extract JSON from the response
        json_str = _extract_json(content)
        if json_str:
            result = json.loads(json_str)
            logger.info(f"Comedy analysis generated for: {title[:50]}...")
            return result

    except ImportError:
        logger.warning("openai package not installed; using fallback analysis.")
    except Exception as e:
        logger.warning(f"OpenAI analysis failed: {e}")

    return None


def _extract_json(text: str) -> Optional[str]:
    """Try to extract a JSON object from text that may contain markdown or other content."""
    # Look for JSON between ```json ... ``` or just {...}
    import re

    # Try fenced code blocks first
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try finding a JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    return None


def fallback_comedy_analysis(title: str, description: str) -> Dict[str, Any]:
    """Generate a basic comedy analysis without AI (fallback).

    Produces a detailed cartoon prompt with speech bubbles/dialog and a punchy one-liner.
    """
    # Extract key nouns/names from the title
    words = title.lower().replace("-", " ").split()
    key_words = [w.strip(".,;:!?'\"") for w in words if len(w) > 3]
    # Pick up to 5 meaningful words
    keywords = list(dict.fromkeys(key_words))[:5]
    kw_text = " ".join(keywords) or "this news story"

    comedian_angle = (
        f"The absurdity of '{title}' is perfect for a satirical cartoon. "
        f"Imagine the irony of {kw_text} happening in real life."
    )

    cartoon_prompt = (
        f"A funny satirical editorial cartoon illustrating the absurdity of {kw_text}. "
        f"Scene: exaggerated caricature-style characters reacting dramatically to the news. "
        f"One character holds a newspaper with a comically large headline. "
        f"Speech bubble on the left: 'You won't believe what just happened!' "
        f"Speech bubble on the right: 'It's so ridiculous it must be true.' "
        f"In the style of a humorous webcomic illustration with bold outlines, "
        f"witty visual humor, and expressive faces. Colorful background with "
        f"chaotic elements representing the news story."
    )

    one_liner = (
        f"'When {keywords[0] if len(keywords) > 0 else 'this'} happens, "
        f"you know we're living in the future.'"
    )

    return {
        "comedian_angle": comedian_angle,
        "cartoon_prompt": cartoon_prompt,
        "one_liner": one_liner,
    }


def analyze_article(article: dict) -> Dict[str, Any]:
    """Full analysis pipeline for one article.

    Tries OpenAI first, falls back to heuristic analysis.
    """
    title = article.get("title", "")
    description = article.get("description", "")

    result = analyze_with_openai(title, description, article.get("url", ""))
    if result:
        result["title"] = title
        result["article_url"] = article.get("url", "")
        return result

    # Fallback
    fallback = fallback_comedy_analysis(title, description)
    fallback["title"] = title
    fallback["article_url"] = article.get("url", "")
    fallback["used_fallback"] = True
    logger.info(f"Used fallback comedy analysis for: {title[:50]}...")
    return fallback
