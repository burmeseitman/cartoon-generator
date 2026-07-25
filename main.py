"""Main entry point for the Cartoon Generator.

Usage:
    python main.py              # Run once — fetches news, generates one cartoon
    python run_service.py       # Run continuously as background service
    python run_service.py --continuous 6  # Every 6 hours
"""
import logging

from config import setup_logging
from news_fetcher import fetch_trending_news, save_fetched_news
from comedian_analyzer import analyze_article
from cartoon_generator import generate_cartoon
from deduplication import is_duplicate, add_to_history, cleanup_old_history


def run_pipeline(max_articles: int | None = 1):
    """Execute one pipeline cycle: fetch news, generate cartoons.

    Args:
        max_articles: Max articles to process (None = all, default 1).
    """
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Cartoon Generator Pipeline Started")
    logger.info("=" * 60)

    cleanup_old_history()

    articles = fetch_trending_news()
    if not articles:
        logger.warning("No articles fetched. Check your internet connection.")
        return

    save_fetched_news(articles)
    logger.info(f"Fetched {len(articles)} articles.")

    processed = 0
    skipped = 0
    generated = 0

    for article in articles:
        if max_articles is not None and processed >= max_articles:
            break

        title = article.get("title", "Untitled")
        logger.info(f"Processing: {title[:80]}...")

        if is_duplicate(title):
            logger.info(f"Skipping duplicate: {title[:50]}...")
            skipped += 1
            continue

        try:
            analysis = analyze_article(article)
            if not analysis:
                logger.warning(f"No comedy analysis for: {title[:50]}...")
                skipped += 1
                continue
        except Exception as e:
            logger.error(f"Analysis failed for {title[:50]}: {e}")
            skipped += 1
            continue

        try:
            result = generate_cartoon(analysis)
            if result:
                generated += 1
                add_to_history({
                    "title": title,
                    "processed_at": result["generated_at"],
                    "cartoon_filename": result["filename"],
                    "one_liner": result.get("one_liner", ""),
                    "article_url": result.get("article_url", ""),
                })
                logger.info(f"Generated cartoon #{generated}: {result['filename']}")
                if result.get("one_liner"):
                    logger.info(f"One-liner: \"{result['one_liner']}\"")
            else:
                logger.warning(f"Failed to generate image for: {title[:50]}...")
                skipped += 1
        except Exception as e:
            logger.error(f"Generation error for {title[:50]}: {e}")
            skipped += 1

        processed += 1

    logger.info("=" * 60)
    logger.info(f"Pipeline Complete. Generated: {generated}, Skipped: {skipped}")
    logger.info("=" * 60)


if __name__ == "__main__":
    setup_logging()
    run_pipeline()
