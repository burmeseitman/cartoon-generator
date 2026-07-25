"""Background service runner for Cartoon Generator.

Runs the pipeline continuously at a configurable interval.
"""
import logging
import signal
import sys
import time
from datetime import datetime

from config import LOG_FILE

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run_pipeline():
    """Run one full cycle of the cartoon generation pipeline."""
    from news_fetcher import fetch_trending_news, save_fetched_news
    from comedian_analyzer import analyze_article
    from cartoon_generator import generate_cartoon
    from deduplication import is_duplicate, add_to_history, cleanup_old_history

    logger.info("=" * 60)
    logger.info(f"Cartoon Generator started at {datetime.now().isoformat()}")
    logger.info("=" * 60)

    # Clean up old history periodically
    cleanup_old_history()

    # Step 1: Fetch news
    articles = fetch_trending_news()
    if not articles:
        logger.warning("No articles fetched. Exiting.")
        return

    save_fetched_news(articles)
    logger.info(f"Fetched {len(articles)} articles.")

    processed = 0
    skipped = 0
    generated = 0

    # Step 2-4: Process each article
    for article in articles:
        title = article.get("title", "Untitled")
        logger.info(f"Processing: {title[:80]}...")

        # Deduplication check
        if is_duplicate(title):
            logger.info(f"Skipping duplicate: {title[:50]}...")
            skipped += 1
            continue

        # Comedian analysis
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

        # Generate cartoon
        try:
            result = generate_cartoon(analysis)
            if result:
                generated += 1
                # Add to history
                add_to_history({
                    "title": title,
                    "processed_at": datetime.now().isoformat(),
                    "cartoon_filename": result["filename"],
                    "one_liner": result.get("one_liner", ""),
                    "article_url": result.get("article_url", ""),
                })
                logger.info(f"Successfully generated cartoon #{generated}: {result['filename']}")
            else:
                logger.warning(f"Failed to generate image for: {title[:50]}...")
                skipped += 1
        except Exception as e:
            logger.error(f"Image generation failed for {title[:50]}: {e}")
            skipped += 1

        processed += 1
        logger.info(f"Progress: {processed}/{len(articles)} articles processed.")

    logger.info(f"Cycle complete. Generated: {generated}, Skipped: {skipped}")


def main():
    """Main entry point for background service."""
    setup_logging()
    logger.info("Cartoon Generator Background Service starting...")

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal. Exiting gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run once or continuously?
    continuous = len(sys.argv) > 1 and sys.argv[1] == "--continuous"
    interval_hours = float(sys.argv[2]) if len(sys.argv) > 2 else 6

    if continuous:
        logger.info(f"Running in continuous mode, interval: {interval_hours} hours")
        while True:
            try:
                run_pipeline()
            except Exception as e:
                logger.error(f"Pipeline error: {e}", exc_info=True)
            logger.info(f"Next run in {interval_hours} hours...")
            time.sleep(interval_hours * 3600)
    else:
        logger.info("Running single pass (add --continuous for repeated runs)")
        run_pipeline()


if __name__ == "__main__":
    main()
