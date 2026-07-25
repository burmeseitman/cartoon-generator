"""Background service runner for Cartoon Generator.

Runs the pipeline continuously at a configurable interval.
"""
import logging
import signal
import sys
import time
from datetime import datetime

from config import setup_logging
from main import run_pipeline

logger = logging.getLogger(__name__)


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
                run_pipeline(max_articles=None)
            except Exception as e:
                logger.error(f"Pipeline error: {e}", exc_info=True)
            logger.info(f"Next run in {interval_hours} hours...")
            time.sleep(interval_hours * 3600)
    else:
        logger.info("Running single pass (add --continuous for repeated runs)")
        run_pipeline(max_articles=None)


if __name__ == "__main__":
    main()
