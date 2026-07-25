"""Tests for deduplication module."""
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from deduplication import _titles_are_similar


class TestTitlesAreSimilar:
    def test_exact_match(self):
        assert _titles_are_similar("hello world", "hello world")

    def test_high_jaccard_similarity(self):
        assert _titles_are_similar(
            "AI model breaks records",
            "AI model breaks new records",
        )

    def test_low_similarity(self):
        assert not _titles_are_similar(
            "Weather forecast today",
            "Stock market update",
        )

    def test_substring_match_short(self):
        assert not _titles_are_similar("hi", "hello world")

    def test_one_contains_the_other(self):
        assert _titles_are_similar(
            "Breaking: AI model breaks records in test",
            "AI model breaks records",
        )

    def test_empty_strings(self):
        assert not _titles_are_similar("", "hello")
        assert not _titles_are_similar("hello", "")

    def test_case_insensitivity(self):
        assert _titles_are_similar("Hello World", "hello world")

    def test_different_casing_and_substring(self):
        assert _titles_are_similar(
            "OpenAI releases GPT-5",
            "openai releases gpt-5 details",
        )


class TestHistoryFileManagement:
    """Integration-style tests for history file read/write."""

    @pytest.fixture
    def temp_history(self, tmp_path: Path):
        """Create a temporary history file path."""
        from deduplication import HISTORY_FILE
        import deduplication as mod

        original = mod.HISTORY_FILE
        test_file = tmp_path / "history.json"
        mod.HISTORY_FILE = test_file
        yield test_file
        mod.HISTORY_FILE = original

    def test_load_nonexistent_file(self, temp_history):
        from deduplication import load_history
        assert load_history() == []

    def test_save_and_load(self, temp_history):
        from deduplication import save_history, load_history

        entries = [
            {"title": "Test", "processed_at": datetime.now().isoformat()}
        ]
        save_history(entries)
        loaded = load_history()
        assert len(loaded) == 1
        assert loaded[0]["title"] == "Test"

    def test_load_corrupted_json(self, temp_history):
        from deduplication import load_history

        temp_history.write_text("not valid json", encoding="utf-8")
        assert load_history() == []

    def test_is_duplicate_within_window(self, temp_history):
        from deduplication import is_duplicate, save_history

        entry = {
            "title": "AI news today",
            "processed_at": datetime.now().isoformat(),
        }
        save_history([entry])
        assert is_duplicate("AI news today")

    def test_not_duplicate_outside_window(self, temp_history):
        from deduplication import is_duplicate, save_history

        old_date = datetime.now() - timedelta(days=60)
        entry = {
            "title": "Old AI news",
            "processed_at": old_date.isoformat(),
        }
        save_history([entry])
        assert not is_duplicate("Old AI news", window_days=30)
