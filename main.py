"""Main entry point for the Cartoon Generator.

Usage:
    python main.py              # Run once
    python run_service.py       # Run continuously as background service
    python run_service.py --continuous 6  # Every 6 hours
"""
import logging
import sys

from config import LOG_FILE
from news_fetcher import fetch_trending_news, save_fetched_news
from comedian_analyzer import analyze_article
from cartoon_generator import generate_cartoon
from deduplication import is_duplicate, add_to_history, cleanup_old_history


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run_pipeline():
    """Execute one full pipeline cycle."""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Cartoon Generator Pipeline Started")
    logger.info("=" * 60)

    # Clean up old history
    cleanup_old_history()

    # Step 1: Fetch trending news
    articles = fetch_trending_news()
    if not articles:
        logger.warning("No articles fetched. Check your internet connection.")
        return

    save_fetched_news(articles)
    logger.info(f"Fetched {len(articles)} articles.\n")

    generated_count = 0

    for i, article in enumerate(articles, 1):
        title = article.get("title", "Untitled")
        logger.info(f"[{i}/{len(articles)}] Processing: {title[:80]}...")

        # Step 2: Deduplication check
        if is_duplicate(title):
            logger.info(f"  -> Skipped (duplicate within 30 days)\n")
            continue

        # Step 3: Comedian analysis
        try:
            analysis = analyze_article(article)
            if not analysis:
                logger.warning(f"  -> No comedy analysis available\n")
                continue
        except Exception as e:
            logger.error(f"  -> Analysis failed: {e}\n")
            continue

        # Step 4: Generate cartoon
        try:
            result = generate_cartoon(analysis)
            if result:
                generated_count += 1
                add_to_history({
                    "title": title,
                    "processed_at": result["generated_at"],
                    "cartoon_filename": result["filename"],
                    "one_liner": result.get("one_liner", ""),
                    "article_url": result.get("article_url", ""),
                })
                logger.info(f"  -> Generated: {result['filename']}")
                if result.get("one_liner"):
                    logger.info(f"  -> One-liner: \"{result['one_liner']}\"")
            else:
                logger.warning("  -> Image generation failed\n")
        except Exception as e:
            logger.error(f"  -> Error: {e}\n")

    logger.info("\n" + "=" * 60)
    logger.info(f"Pipeline Complete. Generated {generated_count} cartoons.")
    logger.info("=" * 60)


if __name__ == "__main__":
    setup_logging()
    run_pipeline()
