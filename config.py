"""Configuration and constants for the Cartoon Generator."""
import os
from pathlib import Path


# Base directories
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
CARTOON_DIR = OUTPUT_DIR / "cartoons"
HISTORY_FILE = OUTPUT_DIR / "history.json"

# Ensure output directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
CARTOON_DIR.mkdir(exist_ok=True)

# News sources - free APIs
NEWS_SOURCES = {
    "google_news_ai": {
        "name": "Google News - AI",
        "url": "https://news.google.com/rss/search?q=artificial+intelligence+AI&hl=en-US&gl=US&ceid=US:en",
    },
    "google_news_cyber": {
        "name": "Google News - Cybersecurity",
        "url": "https://news.google.com/rss/search?q=cybersecurity+hacking+data+breach&hl=en-US&gl=US&ceid=US:en",
    },
}

# Alternative news API (requires key)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# OpenAI API for comedy analysis (requires key)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Image generation - Pollinations.ai (free, no API key needed)
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1024&height=1024&nologo=true&seed={seed}"

# Deduplication settings
DEDUP_WINDOW_DAYS = 30

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "cartoon.log"

# Max news articles to process per run
MAX_ARTICLES = 5

# Comedy style presets
COMEDY_STYLES = [
    "satirical cartoon",
    "political cartoon style",
    "funny editorial cartoon",
    "caricature style illustration",
    "humorous webcomic panel",
]
