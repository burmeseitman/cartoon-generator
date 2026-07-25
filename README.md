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

2. Set environment variables:
```bash
export NEWS_API_KEY=your_newsapi_key        # https://newsapi.org
export OPENAI_API_KEY=your_openai_key        # https://platform.openai.com (for comedy analysis)
export CARICATURE_API_KEY=your_api_key       # For caricature/cartoon generation
```

3. Run the generator:
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

## How It Works

1. **News Fetching**: Queries multiple free news sources for trending AI and cybersecurity articles
2. **Comedian Analysis**: Uses LLM to analyze the news from a comedic perspective, finding humorous angles
3. **Deduplication Check**: Compares against the history log to ensure the news hasn't been cartoonified in the past 30 days
4. **Cartoon Generation**: Creates a funny cartoon image based on the comedic interpretation
5. **Output Saving**: Saves the cartoon and metadata to the output folder

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
