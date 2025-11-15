"""Reusable mixins for spider functionality."""

from typing import Any
from urllib.parse import urlparse

from tunai_scrapers.utils.text import extract_text, extract_tokens, split_sentences


class Priority:
    """Request priority constants for consistent scheduling."""

    CRITICAL = 200
    PAGINATION = 100
    THREAD = 50
    POST = 40
    NORMAL = 0
    LOW = -10


class VocabularyMixin:
    """Mixin for spiders that track vocabulary (word frequency and examples).

    Usage:
        class MySpider(VocabularyMixin, TunaiScrapersSpider):
            def parse(self, response):
                text = extract_text(response.text)
                self.update_vocabulary(text)
    """

    MAX_VOCAB_EXAMPLES = 3

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize vocabulary tracking."""
        super().__init__(*args, **kwargs)
        self.freq: dict[str, int] = {}
        self.samples: dict[str, dict[str, Any]] = {}

    def update_vocabulary(self, text: str) -> None:
        """Update vocabulary frequency and samples from text.

        Args:
            text: Text to extract tokens from
        """
        if not text:
            return

        arabic, romanized = extract_tokens(text)
        sentences = split_sentences(text)

        for token in arabic:
            self._add_token_sample(token, "arabic", sentences)

        for token in romanized:
            self._add_token_sample(token, "roman", sentences)

    def _add_token_sample(self, token: str, script: str, sentences: list[str]) -> None:
        """Add a token to vocabulary with example sentences.

        Args:
            token: The word/token to add
            script: Either "arabic" or "roman"
            sentences: List of sentences to search for examples
        """
        self.freq[token] = self.freq.get(token, 0) + 1

        if token not in self.samples:
            examples = self._find_example_sentences(token, sentences)
            self.samples[token] = {"script": script, "examples": examples}

    def _find_example_sentences(self, token: str, sentences: list[str]) -> list[str]:
        """Find example sentences containing the token.

        Args:
            token: Token to search for
            sentences: List of sentences to search

        Returns:
            Up to MAX_VOCAB_EXAMPLES sentences containing the token
        """
        examples = []
        for sent in sentences:
            if token in sent:
                examples.append(sent)
                if len(examples) >= self.MAX_VOCAB_EXAMPLES:
                    break
        return examples

    def get_vocabulary_data(self) -> dict[str, Any]:
        """Get vocabulary data for export.

        Returns:
            Dictionary with vocabulary statistics and samples
        """
        vocab = []
        for word, count in sorted(self.freq.items(), key=lambda x: x[1], reverse=True):
            sample = self.samples.get(word, {})
            vocab.append(
                {
                    "word": word,
                    "count": count,
                    "script": sample.get("script"),
                    "examples": sample.get("examples", []),
                }
            )

        return {
            "total_words": len(self.freq),
            "vocab": vocab,
        }


class ContentExtractionMixin:
    """Mixin for consistent content extraction from web pages.

    Provides standard text extraction with configurable selectors
    and skip patterns.
    """

    CONTENT_SELECTORS = ["article", "main", "div.content", "div.post"]
    TEXT_ELEMENT_SELECTORS = ["h1", "h2", "h3", "p", "li", "blockquote", "div.text"]
    SKIP_SELECTORS = ["script", "style", "nav", "footer", "noscript", "svg", "form", "iframe"]

    def extract_page_text(self, response) -> str:
        """Extract clean text from a response.

        Args:
            response: Scrapy response object

        Returns:
            Extracted and cleaned text
        """
        # use utility function for now, can be customized later
        return extract_text(response.text)

    def extract_title(self, response) -> str | None:
        """Extract page title.

        Args:
            response: Scrapy response object

        Returns:
            Page title or None
        """
        return response.css("title::text").get()

    def extract_metadata(self, response) -> dict[str, str]:
        """Extract common metadata from page.

        Args:
            response: Scrapy response object

        Returns:
            Dictionary with metadata like author, date, etc.
        """
        metadata = {}

        # Author
        author = (
            response.css('meta[name="author"]::attr(content)').get()
            or response.css('meta[property="article:author"]::attr(content)').get()
        )
        if author:
            metadata["author"] = author

        # Date
        date = (
            response.css('meta[property="article:published_time"]::attr(content)').get()
            or response.css("time::attr(datetime)").get()
        )
        if date:
            metadata["date"] = date

        # Description
        description = (
            response.css('meta[name="description"]::attr(content)').get()
            or response.css('meta[property="og:description"]::attr(content)').get()
        )
        if description:
            metadata["description"] = description

        return metadata


class URLValidationMixin:
    """Mixin for URL validation and domain checking."""

    def is_valid_domain(self, url: str, allowed_domains: list[str] | None = None) -> bool:
        """Check if URL belongs to allowed domains.

        Args:
            url: URL to check
            allowed_domains: List of allowed domains (uses spider's if None)

        Returns:
            True if domain is allowed
        """
        if not url:
            return False

        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            if allowed_domains is None:
                allowed_domains = getattr(self, "allowed_domains", [])

            if not allowed_domains:
                return True

            return domain in allowed_domains
        except Exception:
            return False

    def should_skip_url(self, url: str, skip_patterns: tuple[str, ...] | None = None) -> bool:
        """Check if URL should be skipped based on patterns.

        Args:
            url: URL to check
            skip_patterns: Patterns to skip (uses SKIP_PATH_PREFIXES if None)

        Returns:
            True if URL should be skipped
        """
        if not url:
            return True

        try:
            parsed = urlparse(url)
            path = parsed.path

            if skip_patterns is None:
                skip_patterns = getattr(self, "SKIP_PATH_PREFIXES", ())

            if not skip_patterns:
                return False

            return any(path.startswith(pattern) for pattern in skip_patterns)
        except Exception:
            return True
