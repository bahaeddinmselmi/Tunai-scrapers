"""Tunisia-sat spider."""

from collections.abc import Iterator
from typing import Any
from urllib.parse import urlparse

import scrapy
from scrapy.http import Response

from tunai_scrapers.items import TunisiaSatPage, TunisiaSatPost
from tunai_scrapers.mixins import Priority, VocabularyMixin
from tunai_scrapers.spiders.spider_base import TunaiScrapersSpider
from tunai_scrapers.utils.text import extract_text, extract_tokens, split_sentences

MIN_POST_TEXT_LENGTH = 20


class TunisiaSatSpider(VocabularyMixin, TunaiScrapersSpider):
    """Tunisia-sat forum crawler (Scrapy version of collect_tunisia_sat)."""

    name = "tunisia_sat"
    allowed_domains = ["tunisia-sat.com", "www.tunisia-sat.com"]
    start_urls = ["https://www.tunisia-sat.com/"]

    custom_settings = {
        "ITEM_PIPELINES": {
            "tunai_scrapers.pipelines.TunisiaSatPipeline": 100,
        },
    }

    # Paths to skip when crawling
    SKIP_PATH_PREFIXES = (
        "/login",
        "/logout",
        "/register",
        "/members",
        "/account",
        "/whats-new",
        "/help",
        "/search",
        "/tags",
        "/resources",
        "/media",
    )

    DEFAULT_MAX_PAGES = 200

    def __init__(self, max_pages: int | str = 200, *args: Any, **kwargs: Any) -> None:
        super().__init__(max_pages=max_pages, *args, **kwargs)

    def parse(
        self, response: Response
    ) -> Iterator[TunisiaSatPage | TunisiaSatPost | scrapy.Request]:
        """Parse pages and extract content."""
        if not self.should_process_page(response):
            return

        url = response.url

        # Extract thread posts if this is a thread page
        if self._is_thread_url(url):
            yield from self._parse_thread(response)

        # Extract page text
        text = extract_text(response.text)
        if text:
            yield TunisiaSatPage(url=url, text=text)
            self.update_vocabulary(text)

        # Stop if we've hit the limit
        if not self.should_schedule_more():
            return

        # Handle pagination and link following
        yield from self._follow_links(response)

    def _parse_thread(self, response: Response) -> Iterator[TunisiaSatPost]:
        """Extract posts from a thread page."""
        for article in response.css("article.message"):
            post = self._extract_post(article, response.url)
            if post:
                yield post
                self._update_post_vocabulary(post["text"])

    def _extract_post(self, article, thread_url: str) -> TunisiaSatPost | None:
        """Extract a single post from an article element."""
        # Extract post ID
        pid = article.css("::attr(data-content)").get() or article.css("::attr(id)").get() or ""

        # Extract text content
        text = self._extract_post_text(article)
        if not text or len(text) <= MIN_POST_TEXT_LENGTH:
            return None

        # Extract metadata
        author = self._extract_author(article)
        datetime = article.css("time::attr(datetime)").get()

        return TunisiaSatPost(
            source="tunisia-sat",
            thread_url=thread_url,
            post_id=pid,
            author=author,
            datetime=datetime,
            text=text,
        )

    def _extract_post_text(self, article) -> str:
        """Extract text from a post article."""
        content_selector = article.css("div.bbWrapper")
        if content_selector:
            text = " ".join(content_selector.css("::text").getall()).strip()
        else:
            text = " ".join(article.css("::text").getall()).strip()
        return text

    def _extract_author(self, article) -> str | None:
        """Extract author from a post article."""
        # Try multiple selectors for better coverage
        author_el = (
            article.css(".message-name a::text").get()
            or article.css("a.username::text").get()
            or article.css(".username::text").get()
            or article.css("::attr(data-author)").get()  # Fallback to data-author attribute
        )
        return author_el.strip() if author_el else None

    def _update_post_vocabulary(self, text: str) -> None:
        """Update vocabulary from post text."""
        sentences = split_sentences(text)
        if not sentences:
            return

        arabic, roman = extract_tokens(text)
        for token in arabic:
            self._add_token_sample(token, "arabic", sentences)
        for token in roman:
            self._add_token_sample(token, "roman", sentences)

    def _follow_links(self, response: Response) -> Iterator[scrapy.Request]:
        """Follow links with appropriate priorities."""
        url = response.url

        # Handle thread pagination first
        if self._is_thread_url(url):
            next_page = response.css(
                'a[rel="next"]::attr(href), .pageNav-page--next a::attr(href)'
            ).get()
            if next_page:
                next_url = self.normalize_url(url, next_page, self.allowed_domains)
                if next_url:
                    yield scrapy.Request(
                        next_url, callback=self.parse, priority=Priority.PAGINATION
                    )

        # Categorize and follow other links
        links = self._categorize_links(response)

        for next_url in links["threads"]:
            yield scrapy.Request(next_url, callback=self.parse, priority=Priority.THREAD)

        for next_url in links["posts"]:
            yield scrapy.Request(next_url, callback=self.parse, priority=Priority.POST)

        for next_url in links["other"]:
            yield scrapy.Request(next_url, callback=self.parse, priority=Priority.NORMAL)

    def _categorize_links(self, response: Response) -> dict[str, list[str]]:
        """Categorize links by type for prioritization."""
        links = {"threads": [], "posts": [], "other": []}

        for href in response.css("a::attr(href)").getall():
            next_url = self.normalize_url(response.url, href, self.allowed_domains)
            if not next_url:
                continue

            # Skip unwanted paths
            parsed = urlparse(next_url)
            if any(parsed.path.startswith(sp) for sp in self.SKIP_PATH_PREFIXES):
                continue

            # Categorize by link type
            if self._is_thread_url(next_url):
                links["threads"].append(next_url)
            elif "/post-" in next_url:
                links["posts"].append(next_url)
            else:
                links["other"].append(next_url)

        return links

    def _is_thread_url(self, url: str) -> bool:
        """Check if URL is a thread page."""
        try:
            return "/threads/" in urlparse(url).path
        except Exception:
            return False

    def closed(self, reason: str) -> None:
        """Store vocabulary data for pipeline to save."""
        vocab_data = self.get_vocabulary_data()
        vocab_data["site"] = "tunisia-sat.com"
        self.vocab_data = vocab_data
