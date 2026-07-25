"""Deduplication check to avoid generating duplicate cartoons."""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from config import HISTORY_FILE

logger = logging.getLogger(__name__)


def load_history() -> list[dict]:
    """Load the history of previously processed articles."""
    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read history file: {e}")
        return []


def save_history(history: list[dict]):
    """Save the updated history."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(history)} entries to history.")


def is_duplicate(title: str, window_days: int = 30) -> bool:
    """Check if an article title matches any entry in the past N days.

    Uses fuzzy matching on titles and checks the time window.
    Returns True if considered a duplicate.
    """
    history = load_history()
    cutoff = datetime.now() - timedelta(days=window_days)

    title_lower = title.lower().strip()

    for entry in history:
        # Check if within the time window
        entry_time = datetime.fromisoformat(entry.get("processed_at", ""))
        if entry_time < cutoff:
            continue

        # Compare titles
        existing_title = entry.get("title", "").lower().strip()
        if _titles_are_similar(title_lower, existing_title):
            logger.info(
                f"Duplicate detected: '{title[:50]}' matches "
                f"'{existing_title[:50]}' from {entry_time.strftime('%Y-%m-%d')}"
            )
            return True

    return False


def _titles_are_similar(title1: str, title2: str, threshold: float = 0.7) -> bool:
    """Check if two titles are similar enough to be duplicates."""
    if title1 == title2:
        return True

    # Check if one contains the other significantly
    words1 = set(title1.split())
    words2 = set(title2.split())

    if not words1 or not words2:
        return False

    intersection = words1 & words2
    union = words1 | words2

    jaccard = len(intersection) / len(union)
    if jaccard >= threshold:
        return True

    # Check substring match (one title mostly contains the other)
    if len(title1) > 10 and title2 in title1:
        return True
    if len(title2) > 10 and title1 in title2:
        return True

    return False


def add_to_history(entry: dict):
    """Add a new entry to the history log."""
    history = load_history()
    history.append(entry)
    save_history(history)


def cleanup_old_history(max_entries: int = 1000):
    """Remove entries older than the dedup window to keep the file small."""
    history = load_history()
    cutoff = datetime.now() - timedelta(days=60)  # Keep double the window

    original_len = len(history)
    history = [
        e for e in history
        if datetime.fromisoformat(e.get("processed_at", "")).replace(tzinfo=None) > cutoff
    ]

    # Also cap total entries
    if len(history) > max_entries:
        history = history[-max_entries:]

    if len(history) != original_len:
        save_history(history)
        logger.info(f"Cleaned up history: {original_len} -> {len(history)} entries")
