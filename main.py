"""Main entry point for the Cartoon Generator.

Usage:
    python main.py              # Run once — fetches news, picks one, generates one cartoon
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
    """Execute one pipeline cycle: fetch news, pick one article, generate ONE cartoon."""
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

    # Step 2: Pick the FIRST non-duplicate article
    selected = None
    skipped = 0
    for article in articles:
        title = article.get("title", "Untitled")
        if is_duplicate(title):
            skipped += 1
            continue
        selected = article
        break

    if not selected:
        logger.warning("All fetched articles are duplicates. Nothing to process.")
        return

    title = selected.get("title", "Untitled")
    logger.info(f"Selected article: {title[:100]}...\n")

    # Step 3: Comedian analysis
    try:
        analysis = analyze_article(selected)
        if not analysis:
            logger.error("No comedy analysis available.")
            return
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return

    # Step 4: Generate ONE cartoon
    try:
        result = generate_cartoon(analysis)
        if result:
            add_to_history({
                "title": title,
                "processed_at": result["generated_at"],
                "cartoon_filename": result["filename"],
                "one_liner": result.get("one_liner", ""),
                "article_url": result.get("article_url", ""),
            })
            logger.info(f"\nGenerated cartoon: {result['filename']}")
            if result.get("one_liner"):
                logger.info(f"One-liner: \"{result['one_liner']}\"")
            logger.info(f"Saved to: output/cartoons/{result['filename']}")
        else:
            logger.error("Image generation failed after all retries.")
    except Exception as e:
        logger.error(f"Generation error: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("Pipeline Complete. 1 cartoon generated (or attempted).")
    logger.info("=" * 60)


if __name__ == "__main__":
    setup_logging()
    run_pipeline()
