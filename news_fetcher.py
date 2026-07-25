"""Fetches trending AI and cybersecurity news from free sources."""
import json
import logging
import re
import time
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

import requests
from typing import Any, Dict, List

from config import (
    NEWS_SOURCES,
    NEWS_API_KEY,
    NEWS_API_URL,
    MAX_ARTICLES,
    OUTPUT_DIR,
    is_safe_url,
)

logger = logging.getLogger(__name__)


def _sanitize_text(text: str) -> str:
    """Sanitize text from external sources.

    Strips control characters and normalizes whitespace to prevent
    log injection and data corruption.
    """
    # Remove control characters except newline/tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Decode common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    return text.strip()


def _fetch_rss_feed(url: str) -> List[Dict[str, Any]]:
    """Fetch articles from an RSS feed URL.

    Security: validates URL scheme, sets explicit timeout, sanitizes output.
    """
    # Validate URL scheme to prevent SSRF / file:// attacks
    if not url.startswith(("http://", "https://")):
        logger.warning(f"Rejected unsafe URL scheme: {url}")
        return []

    articles = []
    try:
        req = Request(url, headers={"User-Agent": "CartoonGenerator/1.0"})
        with urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")

        # Parse simple RSS XML
        titles = re.findall(r"<title>(.*?)</title>", raw)
        links = re.findall(r"<link>(.*?)</link>", raw)
        descriptions = re.findall(r"<description>(.*?)</description>", raw)
        pub_dates = re.findall(r"<pubDate>(.*?)</pubDate>", raw)

        for i in range(min(len(titles), 15)):  # Limit per source
            # Sanitize description: strip HTML tags and control characters
            desc_clean = re.sub(r"<[^>]+>", "", descriptions[i] if i < len(descriptions) else "").strip()
            # Remove control characters (except newline/tab) to prevent log injection
            desc_clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", desc_clean)
            articles.append(
                {
                    "title": _sanitize_text(titles[i]),
                    "url": links[i] if i < len(links) else "",
                    "description": desc_clean[:500],
                    "published_at": pub_dates[i] if i < len(pub_dates) else datetime.now().isoformat(),
                    "source": "google_news",
                    "fetched_at": datetime.now().isoformat(),
                }
            )
    except URLError as e:
        logger.warning(f"Failed to fetch RSS feed {url}: {e}")
    except Exception as e:
        logger.warning(f"Error parsing RSS feed {url}: {e}")

    return articles


def _fetch_newsapi(key: str) -> List[Dict[str, Any]]:
    """Fetch articles from NewsAPI.org (requires API key)."""
    if not key:
        return []

    categories = [
        ("technology", "artificial intelligence"),
        ("business", "cybersecurity"),
    ]
    articles = []

    for category, q in categories:
        try:
            params = {
                "category": category,
                "q": q,
                "language": "en",
                "pageSize": 5,
                "apiKey": key,
            }
            resp = requests.get(NEWS_API_URL, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for article in data.get("articles", [])[:5]:
                    if article.get("title") and article.get("url"):
                        articles.append(
                            {
                                "title": article["title"],
                                "url": article["url"],
                                "description": (article.get("description") or "")[:500],
                                "published_at": article.get("publishedAt", ""),
                                "source": "newsapi",
                                "fetched_at": datetime.now().isoformat(),
                            }
                        )
            time.sleep(1)  # Rate limit
        except Exception as e:
            logger.warning(f"NewsAPI error for {category}: {e}")

    return articles


def fetch_trending_news() -> List[Dict[str, Any]]:
    """Fetch trending AI and cybersecurity news from all available sources.

    Returns a list of article dicts, deduplicated by title similarity.
    """
    all_articles = []

    # Fetch from RSS feeds (free, no key needed)
    for source_key, source_info in NEWS_SOURCES.items():
        if not is_safe_url(source_info["url"]):
            logger.warning(f"Skipping unsafe news source: {source_info['name']}")
            continue
        logger.info(f"Fetching from {source_info['name']}...")
        articles = _fetch_rss_feed(source_info["url"])
        all_articles.extend(articles)
        time.sleep(1)

    # Fetch from NewsAPI if key is available
    if NEWS_API_KEY:
        logger.info("Fetching from NewsAPI...")
        articles = _fetch_newsapi(NEWS_API_KEY)
        all_articles.extend(articles)

    # Deduplicate by similar titles
    unique = _deduplicate_titles(all_articles)

    # Sort by fetched_at (newest first)
    unique.sort(key=lambda a: a.get("fetched_at", ""), reverse=True)

    logger.info(f"Fetched {len(unique)} unique articles total.")
    return unique[:MAX_ARTICLES]


def _deduplicate_titles(articles: List[Dict[str, Any]], threshold: float = 0.8) -> List[Dict[str, Any]]:
    """Remove articles with highly similar titles."""
    unique = []
    for article in articles:
        title = article["title"].lower().strip()
        is_dup = False
        for existing in unique:
            existing_title = existing["title"].lower().strip()
            if _title_similarity(title, existing_title) > threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(article)
    return unique


def _title_similarity(a: str, b: str) -> float:
    """Simple Jaccard similarity on word sets."""
    words_a = set(re.findall(r"\w+", a))
    words_b = set(re.findall(r"\w+", b))
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def save_fetched_news(articles: List[Dict[str, Any]]):
    """Save fetched news to a JSON file for debugging."""
    path = OUTPUT_DIR / "fetched_news.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(articles)} articles to {path}")
