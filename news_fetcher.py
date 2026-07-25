"""Fetches trending AI and cybersecurity news from free sources."""
import json
import logging
import re
import time
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

import requests

from config import (
    NEWS_SOURCES,
    NEWS_API_KEY,
    NEWS_API_URL,
    MAX_ARTICLES,
    OUTPUT_DIR,
)

logger = logging.getLogger(__name__)


def _fetch_rss_feed(url: str) -> list[dict]:
    """Fetch articles from an RSS feed URL."""
    articles = []
    try:
        req = Request(url, headers={"User-Agent": "CartoonGenerator/1.0"})
        with urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")

        # Parse simple RSS XML
        titles = re.findall(r"<title>(.*?)</title>", raw)
        links = re.findall(r"<link>(.*?)</link>", raw)
        descriptions = re.findall(r"<description>(.*?)</description>", raw)
        pub_dates = re.findall(r"<pubDate>(.*?)</pubDate>", raw)

        for i in range(min(len(titles), 15)):  # Limit per source
            desc_clean = re.sub(r"<[^>]+>", "", descriptions[i] if i < len(descriptions) else "").strip()
            articles.append(
                {
                    "title": titles[i].replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">"),
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


def _fetch_newsapi(key: str) -> list[dict]:
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


def fetch_trending_news() -> list[dict]:
    """Fetch trending AI and cybersecurity news from all available sources.

    Returns a list of article dicts, deduplicated by title similarity.
    """
    all_articles = []

    # Fetch from RSS feeds (free, no key needed)
    for source_key, source_info in NEWS_SOURCES.items():
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


def _deduplicate_titles(articles: list[dict], threshold: float = 0.8) -> list[dict]:
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


def save_fetched_news(articles: list[dict]):
    """Save fetched news to a JSON file for debugging."""
    path = OUTPUT_DIR / "fetched_news.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(articles)} articles to {path}")
