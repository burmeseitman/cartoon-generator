"""Configuration and constants for the Cartoon Generator."""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.resolve()

# Load .env file if it exists (simple parser, no python-dotenv dependency)
_ENV_PATH = BASE_DIR / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip inline comments (e.g., "value  # comment")
            if "#" in value:
                value = value[:value.index("#")]
            value = value.strip().strip("\"'")
            os.environ.setdefault(key, value)

# Configurable output directory (env: CARTOON_OUTPUT_DIR)
OUTPUT_DIR = Path(os.getenv("CARTOON_OUTPUT_DIR", str(BASE_DIR / "output")))
CARTOON_DIR = OUTPUT_DIR / "cartoons"
HISTORY_FILE = OUTPUT_DIR / "history.json"

# Configurable image filename format (env: IMAGE_FILENAME_FORMAT)
# Available placeholders: {description}, {datetime}, {date}, {time}
# Example: "{description}_{datetime}" -> "claude-ai-20260725_233400.jpg"
IMAGE_FILENAME_FORMAT = os.getenv(
    "IMAGE_FILENAME_FORMAT",
    "{description}_{datetime}"
)

# Ensure output directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CARTOON_DIR.mkdir(parents=True, exist_ok=True)

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

# Gemini API for image generation (primary, needs API key)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-image-preview")
GEMINI_IMAGE_SIZE = os.getenv("GEMINI_IMAGE_SIZE", "1K")

# Pollinations.ai (fallback, free, no API key needed)
POLLINATIONS_BASE_URL = "https://image.pollinations.ai"

# Deduplication settings
DEDUP_WINDOW_DAYS = 30

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "cartoon.log"


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


def sanitize_filename(text: str, max_length: int = 40) -> str:
    """Sanitize text for use in a filename.

    - Lowercases everything
    - Replaces spaces with hyphens
    - Removes characters that are not alphanumeric, hyphens, or underscores
    - Strips leading/trailing dots and hyphens (path traversal protection)
    - Truncates to max_length
    """
    text = text.lower().strip()
    text = text.replace(" ", "-")
    text = "".join(c if c.isalnum() or c in "-_." else "" for c in text)
    # Strip leading dots (prevents .env, .git, etc. attacks) and trailing dots
    text = text.strip(".")
    return text[:max_length]


def build_filename(description: str, ext: str = ".jpg") -> str:
    """Build the image filename using the configured format.

    Args:
        description: Short description of the cartoon/news topic.
        ext: File extension including the dot (default: .jpg).

    Returns:
        A filename like 'claude-ai-20260725_233400.jpg'
    """
    now = datetime.now()
    datetime_str = now.strftime("%Y%m%d_%H%M%S")
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")

    # Sanitize the description for filename safety
    safe_desc = sanitize_filename(description, max_length=50)

    replacements = {
        "{description}": safe_desc,
        "{datetime}": datetime_str,
        "{date}": date_str,
        "{time}": time_str,
    }

    fmt = IMAGE_FILENAME_FORMAT
    for placeholder, value in replacements.items():
        fmt = fmt.replace(placeholder, value)

    # Ensure the extension matches
    for placeholder in replacements:
        if fmt.endswith(placeholder):
            fmt = fmt.replace(placeholder, "") + ext

    if not fmt.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        fmt += ext

    return fmt


def is_safe_url(url: str) -> bool:
    """Validate that a URL uses a safe scheme.

    Only allows http:// and https://. Rejects file://, ftp://, etc.
    to prevent SSRF attacks.
    """
    url_lower = url.strip().lower()
    return url_lower.startswith(("http://", "https://"))

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
