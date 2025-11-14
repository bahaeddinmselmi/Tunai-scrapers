"""Scrapy settings."""

BOT_NAME = "tunai_scrapers"

SPIDER_MODULES = ["tunai_scrapers.spiders"]
NEWSPIDER_MODULE = "tunai_scrapers.spiders"

USER_AGENT = "Mozilla/5.0 (compatible; TunaiParser/0.1; +https://example.com/bot)"

ROBOTSTXT_OBEY = True

TELNETCONSOLE_ENABLED = False
COOKIES_ENABLED = False

LOG_LEVEL = "INFO"

# Performance settings - optimized to match/exceed original speed
# Original is single-threaded with 0.15s delay between requests
# We use concurrency to achieve similar overall request rate but faster
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 16  # All to same domain
DOWNLOAD_DELAY = 0  # No delay - let autothrottle handle it

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 2.0
# Target ~6-8 concurrent requests to respect server while being fast
# This gives us roughly 0.15s effective delay like original but with parallelism
AUTOTHROTTLE_TARGET_CONCURRENCY = 6.0

# Memory limits - disabled for YouTube API spider
# MEMUSAGE_LIMIT_MB = 150  # Reasonable ceiling
# MEMUSAGE_WARNING_MB = 120  # Warn when approaching limit

REACTOR_THREADPOOL_MAXSIZE = 20

RETRY_ENABLED = True
RETRY_TIMES = 2

DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000

HTTPCACHE_ENABLED = False
