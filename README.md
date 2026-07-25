# Cartoon Generator

A background job that fetches trending AI and cybersecurity news, analyzes them from a comedian's viewpoint, and generates funny cartoon images based on the news articles.

## Features

- Fetches trending AI and cybersecurity news from free APIs
- Analyzes news articles from a comedian/comedy perspective
- Generates funny cartoon images using free image generation APIs
- Deduplication check to avoid generating duplicate cartoons from the past 30 days
- Runs as a background job with no frontend
- Saves output to an `output/` folder

## Requirements

- Python 3.9+
- Free API keys (see below)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Set environment variables (or create a `.env` file):
```bash
# Optional API keys (fallbacks are built-in if these are empty)
export NEWS_API_KEY=your_newsapi_key            # https://newsapi.org
export OPENAI_API_KEY=your_openai_key           # https://platform.openai.com (comedy analysis)

# Output Configuration
export CARTOON_OUTPUT_DIR=./output              # Where generated images are saved
export IMAGE_FILENAME_FORMAT="{description}_{datetime}"  # Filename pattern
```

4. Run the generator:
```bash
python main.py
```

## Project Structure

```
cartoon-generator/
├── main.py              # Entry point - orchestrates the pipeline
├── news_fetcher.py      # Fetches trending AI/cybersecurity news
├── comedian_analyzer.py # Analyzes news from comedian viewpoint
├── cartoon_generator.py # Generates funny cartoon images
├── deduplication.py     # Checks for duplicates in past 30 days
├── config.py            # Configuration and constants
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── LICENSE              # MIT License
└── output/              # Generated cartoons and logs
    ├── cartoons/        # Generated cartoon images
    └── history.json     # History of generated items for deduplication
```

## Architecture

### System Overview

The system consists of **four core modules** orchestrated by `main.py`:

```
News Fetcher → Comedian Analyzer → Cartoon Generator → Output Folder
     │               │                    │
     ▼               ▼                    ▼
Google News RSS   OpenAI / Fallback    Pollinations.ai
NewsAPI (opt.)    Heuristic            Free image gen
```

A **deduplication gate** sits between fetching and analysis, checking `history.json` against a 30-day window to prevent re-processing the same story.

### Pipeline Flow

1. **Fetch** — Queries Google News RSS (free) and optional NewsAPI for trending AI & cybersecurity articles
2. **Deduplicate** — Compares titles using Jaccard similarity; skips articles processed within the past 30 days
3. **Analyze** — Uses OpenAI GPT (or built-in heuristic fallback) to generate a comedic angle, cartoon image prompt, and one-liner joke
4. **Generate** — Sends the enhanced prompt to Pollinations.ai (free, no key), validates the image with Pillow, saves it with a configurable filename format
5. **Record** — Adds the article to `history.json` so it won't be reprocessed

### Module Responsibilities

| Module | Responsibility | Key Functions |
|---|---|---|
| `config.py` | Constants, env vars, filename builder | `build_filename()`, `sanitize_filename()`, `is_safe_url()` |
| `news_fetcher.py` | Fetch & parse news from external APIs | `fetch_trending_news()`, `_fetch_rss_feed()`, `_sanitize_text()` |
| `comedian_analyzer.py` | Generate comedy angles & image prompts | `analyze_article()`, `analyze_with_openai()`, `fallback_comedy_analysis()` |
| `cartoon_generator.py` | Generate & save cartoon images | `generate_cartoon()`, `_save_image()`, `_enhance_prompt()` |
| `deduplication.py` | Track processed items, prevent repeats | `is_duplicate()`, `add_to_history()`, `cleanup_old_history()` |
| `main.py` | Pipeline orchestration | `run_pipeline()` |
| `run_service.py` | Continuous background execution | `main()`, `signal_handler()`, `run_pipeline()` |

### Data Model

Each stage transforms the data into a new shape:

| Stage | Key Fields |
|---|---|
| **Article** (from fetcher) | `title`, `url`, `description`, `source`, `fetched_at` |
| **Comedy Analysis** (from analyzer) | `comedian_angle`, `cartoon_prompt`, `one_liner`, `used_fallback` |
| **Cartoon Result** (from generator) | `filename`, `url`, `seed`, `generated_at`, `prompt` |
| **History Entry** (in history.json) | `title`, `processed_at`, `cartoon_filename`, `article_url` |

### Dependencies

| Dependency | Purpose | Required? |
|---|---|---|
| `requests>=2.32.3` | HTTP calls for NewsAPI | Optional (RSS works without it) |
| `Pillow>=10.0.0` | Image validation before saving | Optional (fallback saves without it) |
| `openai` | LLM-powered comedy analysis | Optional (built-in heuristic fallback) |
| Standard library | XML parsing, logging, hashlib, etc. | **Required** |

**Zero external dependencies required** — all three optional dependencies have built-in graceful degradation.

### Security Controls

| Control | Implementation |
|---|---|
| SSRF prevention | URL scheme whitelist (`http://`, `https://` only) via `is_safe_url()` |
| Path traversal | Filename sanitization + resolved path verification stays inside `CARTOON_DIR` |
| Log injection | Control character stripping on all external text |
| Disk DoS | `history.json` capped at 1 MB with auto-cleanup of entries older than 60 days |
| Hanging connections | All HTTP calls have explicit timeouts (30–60s) |
| Malicious payloads | Pillow `Image.verify()` validates images before writing to disk |
| Credential safety | `.env` gitignored; no hardcoded secrets |

See [SECURITY.md](SECURITY.md) for the full threat model.

### Output Configuration

Generated images are saved with a configurable filename format:

| Env Variable | Default | Description |
|---|---|---|
| `CARTOON_OUTPUT_DIR` | `./output` | Directory where cartoons are saved |
| `IMAGE_FILENAME_FORMAT` | `{description}_{datetime}` | Filename template |

**Filename placeholders:**

| Placeholder | Example Value |
|---|---|
| `{description}` | `claude-ai` (sanitized article title) |
| `{datetime}` | `20260725_233400` |
| `{date}` | `20260725` |
| `{time}` | `233400` |

**Example outputs with default format `{description}_{datetime}`:**
```
claude-ai-20260725_233400.jpg
openai-gpt5-release-20260725_233412.jpg
data-breach-mega-corp-20260726_010005.jpg
```

**Example outputs with custom format `{description}_{date}.jpg`:**
```
claude-ai-20260725.jpg
openai-gpt5-release-20260725.jpg
```

Collision handling: if a file with the same name already exists, a numeric suffix is appended (e.g., `claude-ai-20260725_233400_1.jpg`).

## Running as a Background Job

Use cron or systemd to run periodically:

```bash
# Add to crontab with `crontab -e`
# Run every 6 hours
0 */6 * * * cd /path/to/cartoon-generator && python main.py >> logs/cartoon.log 2>&1
```

Or use the included `run_service.py` for continuous background operation:
```bash
python run_service.py
```

## License

MIT License - see LICENSE file
