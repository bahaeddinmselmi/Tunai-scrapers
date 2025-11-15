from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse

import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.http import Response

from tunai_scrapers.config import config


class TunaiScrapersSpider(scrapy.Spider):
    """Base spider class with exact page counting and common functionality.

    This ensures spiders stop after visiting exactly N unique pages,
    matching the behavior of the original collectors for accurate benchmarking.

    Features:
    - Exact page counting (stops after max_pages unique URLs)
    - URL normalization helpers
    - Domain filtering
    - Progress logging
    - Centralized configuration management
    """

    DEFAULT_MAX_PAGES = 100

    def __init__(self, max_pages: int | str | None = None, *args: Any, **kwargs: Any):
        """Initialize spider with page counting.

        Args:
            max_pages: Maximum number of unique pages to visit
        """
        super().__init__(*args, **kwargs)

        self.config = config

        if max_pages is not None:
            self.max_pages = int(max_pages) if isinstance(max_pages, str) else max_pages
        else:
            self.max_pages = self.DEFAULT_MAX_PAGES

        self.pages_visited = 0
        self.visited_urls: set[str] = set()
        self.closing = False

    def should_process_page(self, response: Response) -> bool:
        """Check if we should process this page and update counters.

        Returns True if page should be processed, False if we've hit the limit.

        Args:
            response: The response object to check
        """
        normalized = self.normalize_url(response.url, response.url)
        if not normalized:
            return True

        if self.pages_visited >= self.max_pages:
            if normalized not in self.visited_urls:
                self.logger.info(f"Stopping spider - reached limit {self.max_pages}")
                raise CloseSpider(f"max_pages_reached ({self.max_pages})")
            return False

        # only count new unique URLs
        if normalized not in self.visited_urls:
            self.visited_urls.add(normalized)
            self.pages_visited += 1

            if self.pages_visited % 10 == 0:
                self.logger.info(f"Visited {self.pages_visited}/{self.max_pages} pages")

            if self.pages_visited == self.max_pages:
                self.logger.info(
                    f"Reached max_pages limit ({self.max_pages}) - will process this page then stop"
                )
                self.closing = True

        return True

    def should_schedule_more(self) -> bool:
        """Check if we should schedule more requests.

        Returns:
            True if we should continue scheduling new requests, False otherwise
        """
        return not self.closing

    def normalize_url(
        self, base: str, href: str, allowed_domains: list[str] | None = None
    ) -> str | None:
        """Normalize a URL relative to a base URL.

        Args:
            base: The base URL
            href: The href to normalize (can be relative or absolute)
            allowed_domains: Optional list of allowed domains to filter

        Returns:
            Normalized absolute URL or None if invalid
        """
        if not href:
            return None

        if href.startswith(("javascript:", "mailto:", "#")):
            return None

        try:
            abs_url = urljoin(base, href)
            abs_url, _ = urldefrag(abs_url)
            p = urlparse(abs_url)

            if p.scheme not in ("http", "https"):
                return None

            if allowed_domains and p.netloc not in allowed_domains:
                return None

            return abs_url
        except Exception:
            return None
