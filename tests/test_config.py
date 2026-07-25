"""Tests for config module."""
from config import sanitize_filename, build_filename, is_safe_url


class TestSanitizeFilename:
    def test_lowercases(self):
        assert sanitize_filename("Hello World") == "hello-world"

    def test_replaces_spaces_with_hyphens(self):
        assert sanitize_filename("hello world foo") == "hello-world-foo"

    def test_removes_special_chars(self):
        result = sanitize_filename("hello!@#$world")
        assert result == "helloworld"

    def test_strips_leading_dots(self):
        result = sanitize_filename("..hello")
        assert not result.startswith(".")

    def test_strips_trailing_dots(self):
        result = sanitize_filename("hello..")
        assert not result.endswith(".")

    def test_truncates_to_max_length(self):
        result = sanitize_filename("a" * 100, max_length=20)
        assert len(result) == 20

    def test_preserves_hyphens_and_underscores(self):
        result = sanitize_filename("hello-world_test")
        assert result == "hello-world_test"


class TestBuildFilename:
    def test_includes_extension(self):
        name = build_filename("test", ext=".jpg")
        assert name.endswith(".jpg")

    def test_sanitizes_description(self):
        name = build_filename("HELLO WORLD!", ext=".jpg")
        assert "hello-world" in name

    def test_includes_timestamp(self):
        name = build_filename("test", ext=".jpg")
        # Should contain date in YYYYMMDD format
        parts = name.replace(".jpg", "").split("_")
        assert len(parts) >= 2  # description_datetime


class TestIsSafeUrl:
    def test_accepts_https(self):
        assert is_safe_url("https://example.com")

    def test_accepts_http(self):
        assert is_safe_url("http://example.com")

    def test_rejects_file(self):
        assert not is_safe_url("file:///etc/passwd")

    def test_rejects_ftp(self):
        assert not is_safe_url("ftp://example.com")

    def test_rejects_empty(self):
        assert not is_safe_url("")
