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

### 1. High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CARTOON GENERATOR SYSTEM                             │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌────────────┐  │
│  │   NEWS      │    │   COMEDY    │    │   CARTOON   │    │  OUTPUT    │  │
│  │  FETCHER    │───▶│   ANALYZER  │───▶│ GENERATOR   │───▶│ FOLDER     │  │
│  │             │    │             │    │             │    │            │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └────────────┘  │
│         │                  │                  │                            │
│         ▼                  ▼                  ▼                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │ Google News │    │  OpenAI     │    │Pollinations │                     │
│  │ RSS Feeds   │    │  (GPT)      │    │  .ai (free) │                     │
│  │             │    │             │    │             │                     │
│  │ NewsAPI.org │    │  Fallback   │    │  .jpg/.png  │                     │
│  │ (optional)  │    │  Heuristic  │    │  files      │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│         │                  │                  │                            │
│         └──────────────────┼──────────────────┘                            │
│                            ▼                                               │
│                  ┌─────────────────┐                                       │
│                  │  DEDUPLICATION   │                                       │
│                  │  CHECK (30-day)  │                                       │
│                  └────────┬────────┘                                       │
│                           ▼                                                │
│                  ┌─────────────────┐                                       │
│                  │  history.json   │                                       │
│                  │  (local state)  │                                       │
│                  └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Deployment & Runtime Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         BACKGROUND JOB RUNTIME                           │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     Process (Python)                              │   │
│  │                                                                  │   │
│  │  main.py / run_service.py                                        │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                 │   │
│  │  │ Pipeline   │  │ Pipeline   │  │ Pipeline   │                 │   │
│  │  │ Step 1:    │→│ Step 2:    │→│ Step 3:    │                 │   │
│  │  │ Fetch News │  │ Analyze    │  │ Generate   │                 │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                 │   │
│  │        │               │               │                         │   │
│  │        ▼               ▼               ▼                         │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                 │   │
│  │  │ RSS Parser │  │ LLM /      │  │ HTTP DL +  │                 │   │
│  │  │ (XML)      │  │ Heuristic  │  │ Pillow     │                 │   │
│  │  └────────────┘  └────────────┘  └────────────┘                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     Filesystem Layout                             │   │
│  │                                                                  │   │
│  │  output/                                                         │   │
│  │  ├── cartoons/  ← *.jpg generated images                        │   │
│  │  ├── fetched_news.json ← raw articles (debug)                   │   │
│  │  └── history.json    ← dedup state (≤1 MB)                      │   │
│  │                                                                  │   │
│  │  logs/                                                           │   │
│  │  └── cartoon.log    ← application log                          │   │
│  │                                                                  │   │
│  │  .env            ← secrets (gitignored)                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     Scheduling Options                           │   │
│  │                                                                  │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐          │   │
│  │  │  cron    │  │ systemd timer │  │ run_service.py   │          │   │
│  │  │ (manual) │  │ (Linux)      │  │ --continuous     │          │   │
│  │  └──────────┘  └──────────────┘  └──────────────────┘          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3. Pipeline Sequence Diagram

```
  Scheduler    main.py     news_fetcher   comedian_analy   cartoon_gen   deduplicat   Filesystem
     │             │             │               │              │             │            │
     │ ┌───────────┤             │               │              │             │            │
     │ │ trigger   │             │               │              │             │            │
     │ │──────────▶│             │               │              │             │            │
     │ │           │             │               │              │             │            │
     │ │           │run_pipeline()              │              │             │            │
     │ │           │─────────────┤               │              │             │            │
     │ │           │             │               │              │             │            │
     │ │           │             │fetch_trending_news()         │             │            │
     │ │           │             │────┐          │              │             │            │
     │ │           │             │    │Google   │              │             │            │
     │ │           │             │    │News RSS │              │             │            │
     │ │           │             │    └─┐       │              │             │            │
     │ │           │             │     │       │              │             │            │
     │ │           │             │     │NewsAPI│              │             │            │
     │ │           │             │     │(opt.) │              │             │            │
     │ │           │             │     └──┬────┘              │             │            │
     │ │           │             │      │                        │             │            │
     │ │           │             │◀─────┘                        │             │            │
     │ │           │             │articles[]                    │             │            │
     │ │           │             │                               │             │            │
     │ │           │             │               ┌──────────────┘             │            │
     │ │           │             │               │                              │            │
     │ │           │             │               │for each article:             │            │
     │ │           │             │               │                              │            │
     │ │           │             │               │is_duplicate(title)?          │            │
     │ │           │             │               │──────────────┐               │            │
     │ │           │             │               │              │               │load_history│
     │ │           │             │               │              │               │─────────▶│
     │ │           │             │               │              │               │          │
     │ │           │             │               │◀═════════════│══════════════│history[]  │
     │ │           │             │               │  not dup / skip              │          │
     │ │           │             │               │                              │            │
     │ │           │             │               │analyze_article(article)     │            │
     │ │           │             │               │────┐                         │            │
     │ │           │             │               │    │OpenAI call (if key)    │            │
     │ │           │             │               │    │────┐                   │            │
     │ │           │             │               │    │    │                  │            │
     │ │           │             │               │    │◀───┘                  │            │
     │ │           │             │               │    │JSON: {angle,prompt,   │            │
     │ │           │             │               │    │  one_liner}           │            │
     │ │           │             │               │    │                       │            │
     │ │           │             │               │    │fallback if no key     │            │
     │ │           │             │               │◀───┘                       │            │
     │ │           │             │               │◀────┘                      │            │
     │ │           │             │               │analysis[]                 │            │
     │ │           │             │               │                            │            │
     │ │           │             │               │generate_cartoon(analysis)  │            │
     │ │           │             │               │────┐                       │            │
     │ │           │             │               │    │enhance prompt         │            │
     │ │           │             │               │    │────┐                 │            │
     │ │           │             │               │    │    │HTTP GET         │            │
     │ │           │             │               │    │    │────┐            │            │
     │ │           │             │               │    │    │    │Pollinations│            │
     │ │           │             │               │    │    │    │.ai API     │            │
     │ │           │             │               │    │    │    │──────────▶│            │
     │ │           │             │               │    │    │    │            │            │
     │ │           │             │               │    │    │◀───┘            │            │
     │ │           │             │               │    │    │image bytes      │            │
     │ │           │             │               │    │◀───┘                 │            │
     │ │           │             │               │    │                      │            │
     │ │           │             │               │    │Pillow verify()       │            │
     │ │           │             │               │    │                      │            │
     │ │           │             │               │    │build_filename()      │            │
     │ │           │             │               │    │────┐                 │            │
     │ │           │             │               │    │    │write to disk    │            │
     │ │           │             │               │    │    │────┐            │            │
     │ │           │             │               │    │    │    │*.jpg file  │            │
     │ │           │             │               │    │    │◀───┘            │            │
     │ │           │             │               │    │◀───┘                 │            │
     │ │           │             │               │    │result[]             │            │
     │ │           │             │               │◀───┘                      │            │
     │ │           │             │               │                            │            │
     │ │           │             │               │add_to_history(entry)      │            │
     │ │           │             │               │───────────┐               │            │
     │ │           │             │               │           │               │write history│
     │ │           │             │               │           │               │────────────▶│
     │ │           │             │               │           │               │             │
     │ │           │             │               │◀══════════│══════════════│updated[]    │
     │ │           │             │               │                            │             │
     │ │           │             │             next article...                │             │
     │ │           │             │                                            │             │
     │ │           │◀═════════════════════════════════════════════════════════│             │
     │ │           │summary: N generated, M skipped                          │             │
     │ │ ◀─────────┤                                                            │
     │ │  done                                                                     │
```

### 4. Module Interaction Map

```
                    ┌─────────────────────────────────────────┐
                    │              config.py                  │
                    │  ┌───────────────────────────────────┐  │
                    │  │ ENV VARS: CARTOON_OUTPUT_DIR      │  │
                    │  │         IMAGE_FILENAME_FORMAT     │  │
                    │  │         NEWS_API_KEY              │  │
                    │  │         OPENAI_API_KEY            │  │
                    │  │  ┌─────────────────────────────┐  │  │
                    │  │  │ CONSTANTS:                    │  │  │
                    │  │  │   MAX_ARTICLES = 5            │  │  │
                    │  │  │   DEDUP_WINDOW_DAYS = 30      │  │  │
                    │  │  │   MAX_HISTORY_SIZE = 1MB      │  │  │
                    │  │  │   NEWS_SOURCES (RSS URLs)     │  │  │
                    │  │  │   POLLINATIONS_BASE_URL       │  │  │
                    │  │  └─────────────────────────────┘  │  │
                    │  │  ┌─────────────────────────────┐  │  │
                    │  │  │ HELPERS:                      │  │  │
                    │  │  │   sanitize_filename(text)     │  │  │
                    │  │  │   build_filename(desc)        │  │  │
                    │  │  │   is_safe_url(url)            │  │  │
                    │  │  └─────────────────────────────┘  │  │
                    │  └───────────────────────────────────┘  │
                    └────────┬────────┬────────┬────────┬─────┘
                             │        │        │        │
              ┌──────────────┘        │        │        └──────────────┐
              ▼                        │        │                       ▼
     ┌─────────────────┐              │        │            ┌─────────────────┐
     │  news_fetcher.py │              │        │            │ cartoon_generator│
     │                  │              │        │            │                 │
     │ fetches news →   │              │        │            │ downloads image │
     │ articles[]       │              │        │            │ validates PNG/JPG│
     │                  │              │        │            │ saves to disk   │
     └────────┬─────────┘              │        │            └────────┬────────┘
              │                        │        │                    │
              │  articles[]            │        │   result[]          │
              ▼                        │        │                    ▼
     ┌─────────────────┐              │        │            ┌─────────────────┐
     │ comedian_analy-  │              │        │            │   deduplication │
     │ zer.py           │              │        │            │   .py            │
     │                  │              │        │            │                 │
     │ LLM or heuristic │              │        │            │ is_duplicate()  │
     │ → analysis dict  │              │        │            │ add_to_history()│
     │                  │              │        │            │ cleanup()       │
     └────────┬─────────┘              │        │            └────────┬────────┘
              │                        │        │                    │
              │  analysis[]            │        │   history[]         │
              ▼                        │        │                    ▼
     ┌─────────────────────────────────┴────────┴─────────────────────────┐
     │                            main.py                                  │
     │   Orchestrates the pipeline: fetch → dedup → analyze → generate    │
     │   Logs progress, counts generated/skipped, writes summary          │
     └────────────────────────────────────────────────────────────────────┘
```

### 5. Data Model

```
┌─────────────────────────────────────────────────────────────────────┐
│ ARTICLE (from news_fetcher)                                          │
│ ┌──────────────────┬───────────────────────────────────────────────┐│
│ │ title            │ "Anthropic Releases Claude Opus 2"            ││
│ │ url              │ "https://example.com/news/..."                ││
│ │ description      │ "Short summary of the article..."             ││
│ │ published_at     │ "2026-07-25T14:30:00Z"                        ││
│ │ source           │ "google_news" / "newsapi"                     ││
│ │ fetched_at       │ "2026-07-25T15:00:00+08:00"                   ││
│ └──────────────────┴───────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
         │
         │ comedian_analyzer.analyze_article()
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ COMEDY_ANALYSIS (from comedian_analyzer)                            │
│ ┌──────────────────┬───────────────────────────────────────────────┐│
│ │ comedian_angle   │ "The irony of AI writing jokes about itself..."││
│ │ cartoon_prompt   │ "A funny satirical cartoon showing..."        ││
│ │ one_liner        │ "When AI writes jokes about AI..."            ││
│ │ title            │ (copy from article)                           ││
│ │ article_url      │ (copy from article)                           ││
│ │ used_fallback    │ true/false                                    ││
│ └──────────────────┴───────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
         │
         │ cartoon_generator.generate_cartoon()
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ CARTOON_RESULT (from cartoon_generator)                             │
│ ┌──────────────────┬───────────────────────────────────────────────┐│
│ │ filename         │ "anthropic-claude-20260725_150000.jpg"        ││
│ │ url              │ Pollinations generation URL                   ││
│ │ seed             │ 3847562910                                    ││
│ │ prompt           │ Enhanced cartoon prompt                       ││
│ │ generated_at     │ "2026-07-25T15:00:05+08:00"                   ││
│ │ one_liner        │ (copy from analysis)                          ││
│ │ comedian_angle   │ (copy from analysis)                          ││
│ │ title            │ (copy from article)                           ││
│ │ article_url      │ (copy from article)                           ││
│ └──────────────────┴───────────────────────────────────────────────┘│
│         │                                                           │
│         │ saved to: output/cartoons/<filename>                      │
└─────────────────────────────────────────────────────────────────────┘
         │
         │ deduplication.add_to_history()
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ HISTORY_ENTRY (in history.json)                                     │
│ ┌──────────────────┬───────────────────────────────────────────────┐│
│ │ title            │ "Anthropic Releases Claude Opus 2"            ││
│ │ processed_at     │ "2026-07-25T15:00:05+08:00"                   ││
│ │ cartoon_filename │ "anthropic-claude-20260725_150000.jpg"        ││
│ │ one_liner        │ (copy from analysis)                          ││
│ │ article_url      │ (copy from article)                           ││
│ └──────────────────┴───────────────────────────────────────────────┘│
│         │                                                           │
│         │ stored in: output/history.json                            │
└─────────────────────────────────────────────────────────────────────┘
```

### 6. Security Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SECURITY CONTROLS                            │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  INPUT VALIDATION │  │  URL SANITIZATION│  │  PATH PROTECTION │  │
│  │                  │  │                  │  │                  │  │
│  │ • Control chars  │  │ • Scheme whitelist│  │ • No ../ in     │  │
│  │   stripped       │  │   http/https only│  │   filenames      │  │
│  │ • HTML entities  │  │ • SSRF prevention│  │ • Resolved path │  │
│  │   decoded safely │  │   blocks file:// │  │   verification  │  │
│  │ • Max length caps│  │   ftp:// etc.    │  │ • Inside        │  │
│  │   (500 desc,     │  │                  │  │   CARTOON_DIR   │  │
│  │    50 filename)  │  │                  │  │                  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│           │                     │                     │              │
│           └─────────────────────┼─────────────────────┘              │
│                                 ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    RUNTIME SAFETY                             │   │
│  │                                                               │   │
│  │  • All HTTP calls have explicit timeouts (30-60s)            │   │
│  │  • No eval/exec/os.system in codebase                         │   │
│  │  • SSL verification never disabled                            │   │
│  │  • Image validated with Pillow.verify() before write          │   │
│  │  • history.json capped at 1 MB (DoS protection)               │   │
│  │  • .env never committed (.gitignore)                           │   │
│  │  • No hardcoded secrets — all via environment variables       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    THREAT MODEL                               │   │
│  │                                                               │   │
│  │  Threat              │ Mitigation                            │   │
│  │  ────────────────────┼────────────────────────────────────── │   │
│  │  SSRF via news URL   │ is_safe_url() scheme whitelist         │   │
│  │  Path traversal      │ Filename sanitization + resolve check  │   │
│  │  Log injection       │ Control char stripping                 │   │
│  │  Disk DoS            │ 1 MB history cap + auto-cleanup        │   │
│  │  Slow servers        │ Explicit timeouts on all connections   │   │
│  │  Malicious images    │ Pillow.verify() before writing         │   │
│  │  Credential theft    │ .env gitignored; no hardcoded keys     │   │
│  └──────────────────────┴────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 7. Module Responsibilities

| Module | Responsibility | Key Functions |
|---|---|---|
| `config.py` | Constants, env vars, filename builder | `build_filename()`, `sanitize_filename()`, `is_safe_url()` |
| `news_fetcher.py` | Fetch & parse news from external APIs | `fetch_trending_news()`, `_fetch_rss_feed()`, `_sanitize_text()` |
| `comedian_analyzer.py` | Generate comedy angles & image prompts | `analyze_article()`, `analyze_with_openai()`, `fallback_comedy_analysis()` |
| `cartoon_generator.py` | Generate & save cartoon images | `generate_cartoon()`, `_save_image()`, `_enhance_prompt()` |
| `deduplication.py` | Track processed items, prevent repeats | `is_duplicate()`, `add_to_history()`, `cleanup_old_history()` |
| `main.py` | Pipeline orchestration | `run_pipeline()` |
| `run_service.py` | Continuous background execution | `main()`, `signal_handler()`, `run_pipeline()` |

### 8. Dependencies

| Dependency | Purpose | Required? |
|---|---|---|
| `requests>=2.32.3` | HTTP calls for NewsAPI | Optional (RSS works without it) |
| `Pillow>=10.0.0` | Image validation before saving | Optional (fallback saves without it) |
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
