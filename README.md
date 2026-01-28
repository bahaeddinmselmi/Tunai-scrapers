# 🇹🇳 TunAI Scrapers Collection

> A comprehensive suite of modular data collectors designed to build the largest **Tunisian Arabic (Derja)** dataset for AI training.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-Enabled-green)](https://playwright.dev)
[![Scrapy](https://img.shields.io/badge/Scrapy-Ready-orange)](https://scrapy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 Overview

**TunAI Scrapers** is a specialized toolkit for mining Tunisian dialectal text from the web. It supports multiple platforms and extraction strategies, ensuring a diverse and rich corpus for training Large Language Models (LLMs) and Refined AI Assistants.

### Supported Data Sources
*   **Reddit**: API-based and Headless Browser (Old Reddit) scraping for deep comment threads.
*   **Social Media**: Twitter (X) and Facebook Groups.
*   **Video Platforms**: YouTube transcripts and comments.
*   **Forums**: Targeted scrapers for *Tunisia-Sat* and *Derja Ninja*.
*   **Search Engines**: Specific government/educational domain crawling via Google CSE.

## ⚡ Quick Start

### 1. Installation
This project uses **uv** for fast dependency management.

```bash
# Install dependencies
uv sync

# Install Playwright browsers (for full rendering)
uv run playwright install
```

### 2. Configuration
Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```
*Required keys depend on the collector (e.g., `REDDIT_CLIENT_ID`, `YOUTUBE_API_KEY`).*

## 🕹️ Usage Guide

### 🔴 Reddit
Collect posts and comments from r/Tunisia or other subreddits.
```bash
# Fast API Method
python collectors/collect_reddit.py --sub Tunisia --limit 500 --with_comments

# Playwright Method (Deep Scraping)
python collectors/collect_reddit_playwright.py --sub Tunisia --limit 200 --headed
```

### 🔵 Facebook & Twitter
Mine social sentiment and dialectal variations.
```bash
# Twitter (X)
python collectors/collect_x.py --lang ar --hashtags "تونس,derja"

# Facebook Groups
python collectors/collect_facebook.py --groups <GROUP_ID> --per_group_limit 1000
```

### 🟢 Niche Platforms
Scrape specialized forums for high-quality Derja.
```bash
# Tunisia-Sat Forum
python collectors/collect_tunisia_sat.py --max_pages 500

# Derja Ninja (Vocabulary)
python collectors/collect_derja_ninja.py
```

## 🕷️ Scrapy Data Pipelines
For high-performance crawling, use the Scrapy implementation:
```bash
uv run scrapy crawl tunisia_sat -a max_pages=100
```

## 📂 Project Structure
```
.
├── benchmarks/      # Performance comparison tools
├── collectors/      # Standalone scripts (Reddit, FB, YT, etc.)
├── tunai_scrapers/  # Scrapy spiders project
├── data/            # Output directory
│   ├── raw/
│   └── processed/
└── pyproject.toml
```

## 📄 License
MIT
