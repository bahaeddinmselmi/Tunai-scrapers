# Tunai Parser - Scrapy Framework

Unified scraping framework using Scrapy for better performance and maintainability.

## Architecture

```
tunai_scrapers/
├── items.py          # Data models matching original output format
├── pipelines.py      # Output pipelines for JSONL files
├── settings.py       # Scrapy configuration
├── spiders/          # Spider implementations
└── utils/
    └── text.py       # Shared text extraction utilities
```

## Running Spiders

### Reddit
```bash
scrapy crawl reddit -a sub=Tunisia -a limit=100 -a with_comments=true
```

### Sites
```bash
scrapy crawl sites -a start_urls=https://gov.tn -a domains=gov.tn -a max_pages=100
```

### Tunisia-sat
```bash
scrapy crawl tunisia_sat -a max_pages=200
# Outputs: 
#   data/raw/tunisia_sat_pages.jsonl (raw pages)
#   data/raw/tunisia_sat_posts.jsonl (structured posts)
#   data/processed/tunisia_sat_words.json (vocabulary)
```

### Derja Ninja
```bash
scrapy crawl derja_ninja -a max_pages=150
# Outputs:
#   data/raw/derja_ninja_pages.jsonl (raw pages)
#   data/raw/derja_ninja_cards.jsonl (flashcards)
#   data/processed/derja_ninja_words.json (vocabulary)
```

## Output Format

All spiders produce JSONL files matching the exact format of original collectors in `data/raw/`. Vocabulary spiders also generate JSON vocabulary files in `data/processed/`.

## Performance

- Concurrent requests (8-16 per domain)
- Automatic throttling
- Efficient CSS/XPath selectors (no BeautifulSoup overhead)
- Robots.txt compliance built-in

## Benchmarking

Use existing benchmark system:
```bash
uv run python -m benchmarks.runner --collector sites --limit 100
```
