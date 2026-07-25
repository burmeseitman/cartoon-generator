"""Analyzes news articles from a comedian's viewpoint."""
import json
import logging
from typing import Any

from config import GEMINI_API_KEY, GEMINI_TEXT_MODEL, OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

COMEDY_ANALYSIS_PROMPT = f"""\
You are a stand-up comedian creating a funny cartoon based on a news article.

Given the following news article, provide:
1. A COMEDIAN_ANGLE: One or two sentences capturing the humorous angle of this story
2. A CARTOON_PROMPT: Describe ONLY the scene, character actions, reactions, dialogue in
   speech bubbles, and what makes the situation funny. DO NOT describe visual art style,
   colors, or layout — visual style is added automatically. Follow these rules:

   - ENVIRONMENT: Choose a setting that matches the news topic (e.g. office for business
     news, hospital for healthcare news, classroom for education news, server room for
     cybersecurity news, living room for general tech news, etc.)
   - CHARACTERS: Create 2-5 characters that fit the news context (e.g. office workers,
     doctors, students, IT staff, scientists, or general public). Make them Burmese
     people with casual or work-appropriate clothing. At least one character should
     react dramatically (shock, laughter, facepalm). Include a robot/AI character
     if the news is tech-related (white dome head, blue LED eyes, friendly).
   - ANIMAL: Include one animal (cat, dog, bird) that is completely unbothered by the
     situation — doing something random or lazy, with a deadpan "don't care" expression.
   - DIALOGUE: ALL speech bubble dialogue MUST be in Burmese language (Myanmar script).
   - TITLE: The yellow title banner text should also be in Burmese.
3. A ONE_LINER: A short punchy one-liner joke about this news in Burmese (max 20 words)

Rules:
- Keep it light-hearted and witty, not offensive
- The humor comes from the scene and dialogue, not the art style
- Do NOT include any real person's name; use generic descriptors instead
- At least one dramatic reaction, one unbothered animal — that contrast is the comedy

Format your response as JSON with keys: comedian_angle, cartoon_prompt, one_liner

News Article:
Title: {{title}}
Description: {{description}}
URL: {{url}}
"""


def analyze_with_openai(title: str, description: str, url: str) -> dict[str, Any] | None:
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


def analyze_with_gemini_text(title: str, description: str, url: str) -> dict[str, Any] | None:
    """Use Gemini text model to get a comedian's analysis with correct Burmese.

    Returns a dict with comedian_angle, cartoon_prompt, one_liner.
    Returns None if API is unavailable or fails.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set; skipping Gemini text analysis.")
        return None

    import urllib.request
    from urllib.request import Request

    api_url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_TEXT_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )

    prompt = COMEDY_ANALYSIS_PROMPT.format(title=title, description=description, url=url)

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 1.2,
            "maxOutputTokens": 500,
        },
    }).encode("utf-8")

    try:
        req = Request(
            api_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

        candidates = data.get("candidates", [])
        if not candidates:
            logger.warning("Gemini text returned no candidates.")
            return None

        content = candidates[0].get("content", {}).get("parts", [])
        if not content:
            logger.warning("Gemini text returned no content parts.")
            return None

        text = content[0].get("text", "").strip()
        json_str = _extract_json(text)
        if json_str:
            result = json.loads(json_str)
            logger.info(f"Gemini comedy analysis generated for: {title[:50]}...")
            return result

    except Exception as e:
        logger.warning(f"Gemini text analysis failed: {e}")

    return None


def _extract_json(text: str) -> str | None:
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


def fallback_comedy_analysis(title: str, description: str) -> dict[str, Any]:
    """Generate a basic comedy analysis without AI (fallback).

    Produces a cartoon prompt referencing the family comic style guide.
    """
    words = title.lower().replace("-", " ").split()
    key_words = [w.strip(".,;:!?'\"") for w in words if len(w) > 3]
    keywords = list(dict.fromkeys(key_words))[:4]
    kw_text = " ".join(keywords) or "this news story"

    comedian_angle = (
        f"The irony of '{title}' is perfect for a warm family comic. "
        f"Imagine a cozy living room where the family reacts to {kw_text}."
    )

    cartoon_prompt = (
        f"The family in the living room reacts with surprise to news about {kw_text}. "
        f"The robot shows data about it on the laptop. "
        f"Speech bubbles contain humorous Burmese dialogue expressing shock and reactions. "
        f"Title banner in Burmese text at top."
    )

    one_liner = (
        "ဒီခေတ်ကြီးမှာ ဘာမဆိုဖြစ်နိုင်တယ်နော်။ "
        "(In this era, anything can happen, right?)"
    )

    return {
        "comedian_angle": comedian_angle,
        "cartoon_prompt": cartoon_prompt,
        "one_liner": one_liner,
    }


def analyze_article(article: dict) -> dict[str, Any]:
    """Full analysis pipeline for one article.

    Tries: OpenAI → Gemini text → heuristic fallback.
    """
    title = article.get("title", "")
    description = article.get("description", "")

    # Try OpenAI first (best quality)
    result = analyze_with_openai(title, description, article.get("url", ""))
    if result:
        result["title"] = title
        result["article_url"] = article.get("url", "")
        return result

    # Try Gemini text (correct Burmese dialogue)
    result = analyze_with_gemini_text(title, description, article.get("url", ""))
    if result:
        result["title"] = title
        result["article_url"] = article.get("url", "")
        result["used_fallback"] = False
        return result

    # Heuristic fallback
    fallback = fallback_comedy_analysis(title, description)
    fallback["title"] = title
    fallback["article_url"] = article.get("url", "")
    fallback["used_fallback"] = True
    logger.info(f"Used fallback comedy analysis for: {title[:50]}...")
    return fallback
