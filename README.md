# TunAI Scrapers

Standalone data collection scripts used for building a Tunisian AI assistant. This repo contains modular collectors for Reddit, old Reddit (Playwright), Google CSE, Tunisia-Sat, Derja Ninja, generic sites, YouTube, X/Twitter, and Facebook groups.

## Quick start

1) Create and activate a Python 3.11 venv
- Windows PowerShell
```
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
```

2) Install requirements
```
pip install -r requirements.txt
```

3) Install Playwright browsers (for the old.reddit.com collector)
```
python -m playwright install
```

4) Copy `.env.example` to `.env` and fill credentials as needed
```
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
GOOGLE_API_KEY=your_key
GOOGLE_CX=your_cse_id
X_BEARER_TOKEN=your_token
YOUTUBE_API_KEY=your_key
META_GRAPH_TOKEN=your_token
```

5) Run collectors (outputs go under `data/` by default)
- Reddit via API (posts + optional comments)
```
python collectors/collect_reddit.py --sub Tunisia --limit 300 --with_comments \
  --out_posts data/raw/reddit_posts.jsonl --out_comments data/raw/reddit_comments.jsonl
```
- Old Reddit (Playwright) with comments expansion
```
python collectors/collect_reddit_playwright.py --sub Tunisia --limit 150 --with_comments \
  --out_posts data/raw/reddit_posts_pw.jsonl --out_comments data/raw/reddit_comments_pw.jsonl --headed
```
- Google CSE site-restricted crawl
```
python collectors/collect_google_cse.py --query "دارجة تونسية" --site gov.tn,edu.tn \
  --num 30 --out data/raw/google_cse.jsonl
```
- Tunisia-Sat forum posts + raw pages
```
python collectors/collect_tunisia_sat.py --max_pages 200 \
  --out_vocab data/processed/tunisia_sat_words.json \
  --out_raw data/raw/tunisia_sat_pages.jsonl \
  --out_posts data/raw/tunisia_sat_posts.jsonl
```
- Derja Ninja vocabulary + raw pages + flashcard-like triples
```
python collectors/collect_derja_ninja.py --max_pages 150 \
  --out_vocab data/processed/derja_ninja_words.json \
  --out_raw data/raw/derja_ninja_pages.jsonl \
  --out_cards data/raw/derja_ninja_cards.jsonl
```
- Generic multi-site crawler
```
python collectors/collect_sites.py --start_urls https://www.gov.tn,https://www.pm.gov.tn \
  --domains gov.tn,pm.gov.tn --max_pages 100 --out data/raw/sites.jsonl
```
- YouTube transcripts
```
python collectors/collect_youtube.py --search "darija tunisienne" --pages 2 --out data/raw/youtube_tn.jsonl
```
- X / Twitter recent search (requires token)
```
python collectors/collect_x.py --limit 1000 --out data/raw/x_tn.jsonl --lang ar --hashtags derja,تونس
```
- Facebook group feed (requires proper app permissions)
```
python collectors/collect_facebook.py --groups https://www.facebook.com/groups/<groupid> \
  --out data/raw/facebook_groups.jsonl --per_group_limit 300
```

## Notes
- Respect robots.txt and site terms. The collectors include basic robots checks where applicable.
- Playwright collector persists session storage via `--storage` so you can login once, then reuse.
- Outputs are JSONL for easy downstream processing.

## Structure
- collectors/  # individual scripts
- data/
  - raw/
  - processed/

## License
- Provide your preferred license for redistribution and usage.
