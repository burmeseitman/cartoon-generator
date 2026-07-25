# Cartoon Generator

A background job that fetches trending news across tech, cybersecurity, business, and world topics, analyzes them from a comedian's viewpoint, and generates funny Burmese cartoon-style images with Burmese dialogue.

## Features

- Fetches trending news from 7 topic categories (AI, cybersecurity, tech, science, business, world, social media)
- Random source subset each run for topic diversity
- Analyzes news articles from a comedian/comedy perspective
- Generates funny Burmese cartoon-style images using Gemini API (primary) with Pollinations.ai fallback
- Characters and environments adapt to the news topic (not a fixed family)
- Burmese cartoonist art style — bold ink outlines, watercolor wash, hand-drawn feel
- Burmese language speech bubbles and title banners
- Topic deduplication over 30-day window to avoid repeats
- Runs as a background job with no frontend
- Saves output to an `output/` folder
- 28 unit tests for core modules

## Requirements

- Python 3.10+ (uses `str \| None` and `list[dict]` type hints)
- Gemini API key (primary image generation)
- Optional: OpenAI API key (better comedy analysis; built-in fallback works without it)
- Optional: NewsAPI key (RSS feeds work without it)

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
# Gemini API (primary image generation — highly recommended)
export GEMINI_API_KEY=your_gemini_key           # https://aistudio.google.com

# Optional: OpenAI (better comedy analysis)
export OPENAI_API_KEY=your_openai_key           # https://platform.openai.com

# Optional: NewsAPI (additional news source)
export NEWS_API_KEY=your_newsapi_key            # https://newsapi.org

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
├── main.py                 # Entry point — orchestrates the pipeline
├── news_fetcher.py         # Fetches trending AI/cybersecurity news
├── comedian_analyzer.py    # Analyzes news from comedian viewpoint
├── cartoon_generator.py    # Generates funny cartoon images
├── deduplication.py        # Checks for duplicates in past 30 days
├── config.py               # Configuration and constants
├── run_service.py          # Continuous background execution
├── CARTOON_STYLE_GUIDE.md  # Visual style guide for consistent character designs
├── requirements.txt        # Python dependencies
├── tests/
│   ├── test_config.py      # Config module tests (15 tests)
│   └── test_deduplication.py  # Deduplication module tests (13 tests)
├── README.md               # This file
├── LICENSE                 # MIT License
└── output/                 # Generated cartoons and logs
    ├── cartoons/           # Generated cartoon images
    └── history.json        # History of generated items for deduplication
```

## Architecture

### System Overview

The system consists of **four core modules** orchestrated by `main.py`:

<svg viewBox="0 0 820 340" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:system-ui,-apple-system,sans-serif">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M0,0 L10,5 L0,10 Z" fill="#666"/>
    </marker>
    <marker id="arrow-down" viewBox="0 0 10 10" refX="5" refY="9" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M0,0 L5,10 L10,0 Z" fill="#888"/>
    </marker>
  </defs>

  <!-- horizontal arrows between main boxes -->
  <line x1="195" y1="80" x2="240" y2="80" stroke="#666" stroke-width="2" marker-end="url(#arrow)"/>
  <line x1="405" y1="80" x2="450" y2="80" stroke="#666" stroke-width="2" marker-end="url(#arrow)"/>
  <line x1="615" y1="80" x2="660" y2="80" stroke="#666" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- main boxes -->
  <rect x="20" y="50" width="175" height="60" rx="8" fill="#e3f2fd" stroke="#1e88e5" stroke-width="2"/>
  <text x="107" y="78" text-anchor="middle" fill="#1565c0" font-size="13" font-weight="700">News Fetcher</text>
  <text x="107" y="95" text-anchor="middle" fill="#555" font-size="10">fetch_trending_news()</text>

  <rect x="245" y="50" width="160" height="60" rx="8" fill="#fff3e0" stroke="#fb8c00" stroke-width="2"/>
  <text x="325" y="78" text-anchor="middle" fill="#e65100" font-size="13" font-weight="700">Comedian Analyzer</text>
  <text x="325" y="95" text-anchor="middle" fill="#555" font-size="10">analyze_article()</text>

  <rect x="455" y="50" width="160" height="60" rx="8" fill="#e8f5e9" stroke="#43a047" stroke-width="2"/>
  <text x="535" y="78" text-anchor="middle" fill="#2e7d32" font-size="13" font-weight="700">Cartoon Generator</text>
  <text x="535" y="95" text-anchor="middle" fill="#555" font-size="10">generate_cartoon()</text>

  <rect x="665" y="50" width="140" height="60" rx="8" fill="#f3e5f5" stroke="#8e24aa" stroke-width="2"/>
  <text x="735" y="78" text-anchor="middle" fill="#6a1b9a" font-size="13" font-weight="700">Output</text>
  <text x="735" y="95" text-anchor="middle" fill="#555" font-size="10">cartoons/</text>

  <!-- dedup gate -->
  <rect x="170" y="170" width="110" height="44" rx="20" fill="#fce4ec" stroke="#e53935" stroke-width="2" stroke-dasharray="5,3"/>
  <text x="225" y="197" text-anchor="middle" fill="#c62828" font-size="11" font-weight="600">Dedup Gate</text>

  <!-- vertical connector down from News Fetcher to dedup -->
  <line x1="107" y1="110" x2="107" y2="145" stroke="#888" stroke-width="1.5" stroke-dasharray="4,3"/>
  <line x1="107" y1="145" x2="225" y2="170" stroke="#888" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrow-down)"/>

  <!-- vertical connector up from dedup to Comedian Analyzer -->
  <line x1="225" y1="214" x2="225" y2="235" stroke="#888" stroke-width="1.5" stroke-dasharray="4,3"/>
  <line x1="225" y1="235" x2="325" y2="110" stroke="#888" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrow-down)"/>

  <!-- external services -->
  <rect x="20" y="260" width="175" height="50" rx="6" fill="#f5f5f5" stroke="#999" stroke-width="1.5"/>
  <text x="107" y="280" text-anchor="middle" fill="#444" font-size="11" font-weight="600">Google News RSS</text>
  <text x="107" y="296" text-anchor="middle" fill="#888" font-size="10">NewsAPI (opt)</text>

  <rect x="245" y="260" width="160" height="50" rx="6" fill="#f5f5f5" stroke="#999" stroke-width="1.5"/>
  <text x="325" y="280" text-anchor="middle" fill="#444" font-size="11" font-weight="600">OpenAI / Fallback</text>
  <text x="325" y="296" text-anchor="middle" fill="#888" font-size="10">Heuristic</text>

  <rect x="455" y="260" width="160" height="50" rx="6" fill="#f5f5f5" stroke="#999" stroke-width="1.5"/>
  <text x="535" y="280" text-anchor="middle" fill="#444" font-size="11" font-weight="600">Gemini API</text>
  <text x="535" y="296" text-anchor="middle" fill="#888" font-size="10">Pollinations.ai (fallback)</text>

  <!-- vertical connectors from external services up to main boxes -->
  <line x1="107" y1="260" x2="107" y2="110" stroke="#888" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="325" y1="260" x2="325" y2="110" stroke="#888" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="535" y1="260" x2="535" y2="110" stroke="#888" stroke-width="1" stroke-dasharray="3,3"/>
</svg>

A **deduplication gate** sits between fetching and analysis, checking `history.json` against a 30-day window to prevent re-processing the same story.

### Pipeline Flow

1. **Fetch** — Queries a random subset of Google News RSS feeds (7 topic categories) and optional NewsAPI; fetches up to 20 articles, shuffled for variety
2. **Deduplicate** — Compares titles using Jaccard similarity; skips articles processed within the past 30 days
3. **Analyze** — Uses OpenAI GPT (or built-in heuristic fallback) to generate a comedic angle, scene description, and one-liner joke. The [style guide](CARTOON_STYLE_GUIDE.md) is injected into the AI prompt for consistent character references
4. **Enhance** — Visual style block (character designs, color palette, layout) is prepended to the scene description by `_enhance_prompt()`
5. **Generate** — Sends the combined prompt to Gemini API (primary) with Pollinations.ai fallback, validates the image with Pillow, saves it with a configurable filename format
6. **Record** — Adds the article to `history.json` so it won't be reprocessed

### Cartoon Style

The generator uses a flexible style defined in [CARTOON_STYLE_GUIDE.md](CARTOON_STYLE_GUIDE.md). The environment and characters adapt to the news topic, while the core art style stays consistent:

| Element | Description |
|---|---|
| **Environment** | Adapts to the news — office, hospital, classroom, tea shop, server room, etc. |
| **Characters** | 2-5 Burmese characters fitting the news context; girls/ladies sometimes wear thanaka |
| **Animal** | One "don't care" animal (cat, dog, bird) with deadpan expression or lazy posture — comedic contrast |
| **Art style** | Hand-drawn Burmese cartoon — bold black ink outlines, watercolor wash, hand-painted feel |
| **Speech bubbles** | White rounded ovals with thin ink outlines — **Burmese text** |
| **Title banner** | Yellow banner at top with bold black **Burmese text** |
| **Tone** | Humorous but wholesome, light satire, dramatic reactions + unbothered animal |

### Module Responsibilities

| Module | Responsibility | Key Functions |
|---|---|---|---|
| `config.py` | Constants, env vars, filename builder, logging setup | `build_filename()`, `sanitize_filename()`, `is_safe_url()`, `setup_logging()` |
| `news_fetcher.py` | Fetch & parse news from diverse topic sources | `fetch_trending_news()`, `_fetch_rss_feed()`, `_sanitize_text()` |
| `comedian_analyzer.py` | Generate comedy angles & scene descriptions | `analyze_article()`, `analyze_with_openai()`, `fallback_comedy_analysis()` |
| `cartoon_generator.py` | Generate & save cartoon images | `generate_cartoon()`, `_save_image()`, `_enhance_prompt()`, `_generate_with_gemini()` |
| `deduplication.py` | Track processed items, prevent repeats | `is_duplicate()`, `add_to_history()`, `cleanup_old_history()` |
| `main.py` | Pipeline orchestration | `run_pipeline(max_articles=1)` |
| `run_service.py` | Continuous background execution | `main()`, reuses `main.run_pipeline(max_articles=None)` |

### Data Model

Each stage transforms the data into a new shape:

| Stage | Key Fields |
|---|---|---|
| **Article** (from fetcher) | `title`, `url`, `description`, `source`, `fetched_at` |
| **Comedy Analysis** (from analyzer) | `comedian_angle`, `cartoon_prompt` (scene only), `one_liner` (Burmese), `used_fallback` |
| **Enhanced Prompt** (from generator) | Visual style block + scene description (up to 1000 chars) |
| **Cartoon Result** (from generator) | `filename`, `url`, `seed`, `generated_at`, `prompt`, `source` |
| **History Entry** (in history.json) | `title`, `processed_at`, `cartoon_filename`, `article_url` |

### Dependencies

| Dependency | Purpose | Required? |
|---|---|---|---|
| `requests>=2.32.3` | HTTP calls for NewsAPI | Optional (RSS works without it) |
| `Pillow>=10.0.0` | Image validation before saving | Optional (saves without validation) |
| `openai>=1.0.0` | LLM-powered comedy analysis | Optional (built-in heuristic fallback) |
| Standard library | XML parsing, logging, hashlib, etc. | **Required** |

**Zero external dependencies required** — all dependencies have built-in graceful degradation. The system works with just a Gemini API key.

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

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## Running as a Background Job

Use cron or systemd to run periodically:

```bash
# Add to crontab with `crontab -e`
# Run every 6 hours
0 */6 * * * cd /path/to/cartoon-generator && python main.py >> logs/cartoon.log 2>&1
```

Or use the included `run_service.py` for continuous background operation:
```bash
python run_service.py              # Single pass
python run_service.py --continuous 6  # Every 6 hours
```

## License

MIT License - see LICENSE file
