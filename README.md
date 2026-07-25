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

# Output Configuration (NEW)
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

```
┌─────────────────────────────────────────────────────────────────┐
│                     Cartoon Generator                           │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌────────────┐            │
│  │   News   │───▶│   Comedian   │───▶│   Cartoon  │            │
│  │  Fetcher │    │   Analyzer   │    │ Generator  │            │
│  └──────────┘    └──────────────┘    └────────────┘            │
│       │                   │                   │                  │
│       ▼                   ▼                   ▼                  │
│  ┌──────────┐    ┌──────────────┐    ┌────────────┐            │
│  │  Google  │    │  OpenAI /    │    │ Pollinations│            │
│  │  News RSS│    │ Fallback     │    │   .ai       │            │
│  │  + NewsAPI│   │ (heuristic)  │    │  (free)     │            │
│  └──────────┘    └──────────────┘    └────────────┘            │
│       │                                                       │
│       ▼                                                       │
│  ┌──────────────┐     ┌──────────────────┐                    │
│  │  Deduplication│◀───▶│   Output Folder   │                   │
│  │     Check    │     │  cartoons/*.jpg   │                   │
│  └──────────────┘     └──────────────────┘                    │
│       │                                                       │
│       ▼                                                       │
│  ┌──────────────────┐                                        │
│  │   history.json   │                                        │
│  │  (30-day window) │                                        │
│  └──────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
main.py (Orchestrator)
  │
  ├─► news_fetcher.py          # Data ingestion layer
  │     ├─ _fetch_rss_feed()   # Google News RSS (free, no key)
  │     └─ _fetch_newsapi()    # NewsAPI.org (optional, needs key)
  │           │
  │           └─► deduplicate_titles()  # Intra-source dedup
  │
  ├─► deduplication.py         # Gatekeeper — prevents re-processing
  │     ├─ is_duplicate()      # Fuzzy title match (Jaccard similarity ≥ 0.7)
  │     ├─ load/save_history() # Persistent JSON state
  │     └─ cleanup_old_history()  # Auto-prune entries > 60 days
  │
  ├─► comedian_analyzer.py     # Intelligence layer
  │     ├─ analyze_with_openai()  # GPT-4 → JSON: angle, prompt, one-liner
  │     └─ fallback_comedy_analysis()  # Heuristic fallback (no API needed)
  │
  └─► cartoon_generator.py     # Rendering layer
        ├─ generate_cartoon()
        │     ├─ _enhance_prompt()  # Add style keywords
        │     ├─ _save_image()      # Download + Pillow validate + save
        │     └─ build_filename()   # Configurable name pattern
        └─ Pollinations.ai API    # Free image generation (no key)
```

### Data Flow

```
Article Dict (from fetcher)
  ├── title: str
  ├── url: str
  ├── description: str
  ├── published_at: str
  └── source: str ("google_news" | "newsapi")
        │
        ▼
  Comedy Analysis Dict (from analyzer)
  ├── comedian_angle: str
  ├── cartoon_prompt: str   ← used as image generation prompt
  ├── one_liner: str
  └── title: str            ← used as filename description
        │
        ▼
  Cartoon Result Dict (from generator)
  ├── filename: str         ← e.g., "claude-ai-20260725_233400.jpg"
  ├── url: str              ← Pollinations generation URL
  ├── seed: int             ← deterministic seed for reproducibility
  ├── generated_at: str     ← ISO timestamp
  ├── one_liner: str
  ├── comedian_angle: str
  ├── title: str
  └── article_url: str
        │
        ▼
  History Entry (saved by deduplication)
  ├── title: str
  ├── processed_at: str
  ├── cartoon_filename: str
  ├── one_liner: str
  └── article_url: str
```

### Module Responsibilities

| Module | Responsibility | Key Functions |
|---|---|---|
| `config.py` | Constants, env vars, filename builder | `build_filename()`, `sanitize_filename()` |
| `news_fetcher.py` | Fetch & parse news from external APIs | `fetch_trending_news()`, `_fetch_rss_feed()` |
| `comedian_analyzer.py` | Generate comedy angles & image prompts | `analyze_article()`, `fallback_comedy_analysis()` |
| `cartoon_generator.py` | Generate & save cartoon images | `generate_cartoon()`, `_save_image()` |
| `deduplication.py` | Track processed items, prevent repeats | `is_duplicate()`, `add_to_history()` |
| `main.py` | Pipeline orchestration | `run_pipeline()` |
| `run_service.py` | Continuous background execution | `main()`, `signal_handler()` |

### Dependencies

| Dependency | Purpose | Required? |
|---|---|---|
| `requests` | HTTP calls for NewsAPI | Optional (RSS works without it) |
| `Pillow` | Image validation before saving | Optional (fallback saves without it) |
| `openai` | LLM-powered comedy analysis | Optional (built-in heuristic fallback) |
| Standard library | XML parsing, logging, hashlib, etc. | **Required** |

**Zero external dependencies required** — all three optional dependencies have built-in graceful degradation.

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
