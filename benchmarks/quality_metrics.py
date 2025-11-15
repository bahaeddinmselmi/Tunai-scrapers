"""Universal quality metrics calculation for benchmark results."""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, cast
from urllib.parse import ParseResult, urlparse

JsonItem = dict[str, Any]

TEXT_FIELDS = [
    "text",
    "content",
    "body",
    "message",
    "description",
    "summary",
]

MIN_NONTRIVIAL_TEXT_LENGTH = 50

URL_FIELDS = [
    "url",
    "link",
    "href",
    "source_url",
    "thread_url",
    "post_url",
    "page_url",
]

ID_FIELDS = [
    "id",
    "post_id",
    "comment_id",
    "message_id",
    "item_id",
    "_id",
]

AUTHOR_FIELDS = [
    "author",
    "user",
    "username",
    "user_name",
    "poster",
    "creator",
]

DATE_FIELDS = [
    "date",
    "datetime",
    "timestamp",
    "created_at",
    "posted_at",
    "time",
]

THREAD_ID_PATTERNS = [
    r"/threads/(\d+)",
    r"/t/([^/]+)",
    r"/topic/(\d+)",
    r"/discussion/(\d+)",
]


class MetricsAnalyzer:
    """Analyzes JSONL output files to calculate universal quality metrics."""

    def __init__(self, output_files: list[Path]) -> None:
        """Initialize with list of output files to analyze."""
        self.output_files = output_files
        self.metrics: dict[str, Any] = {}

    def calculate_all_metrics(self) -> dict[str, Any]:
        """Calculate all available metrics from the output files."""
        # collect all items from all files
        all_items: list[JsonItem] = []
        file_stats: dict[str, dict[str, Any]] = {}

        for file_path in self.output_files:
            if not file_path.exists():
                continue

            # only process jsonl files, skip single JSON files
            if file_path.suffix != ".jsonl":
                continue

            items = self._load_jsonl(file_path)
            if items:
                all_items.extend(items)
                file_stats[file_path.name] = {
                    "count": len(items),
                    "file_type": self._guess_file_type(file_path.name, items),
                }

        if not all_items:
            return self.metrics

        self.metrics["total_items"] = len(all_items)
        self.metrics["files_analyzed"] = len(file_stats)

        self._analyze_text_content(all_items)
        self._analyze_urls(all_items)
        self._analyze_identifiers(all_items)
        self._analyze_authors(all_items)
        self._analyze_threads(all_items)
        self._analyze_temporal_data(all_items)

        return self.metrics

    def _load_jsonl(self, file_path: Path) -> list[JsonItem]:
        """Load all items from a JSONL file."""
        items: list[JsonItem] = []
        try:
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        items.append(item)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        return items

    def _guess_file_type(self, filename: str, items: list[JsonItem]) -> str:
        """Guess the type of content based on filename and items."""
        filename_lower = filename.lower()

        if "post" in filename_lower:
            return "posts"
        elif "comment" in filename_lower:
            return "comments"
        elif "page" in filename_lower or "raw" in filename_lower:
            return "pages"

        if items:
            sample = items[0]
            if "thread_url" in sample or "post_id" in sample:
                return "posts"
            elif "comment" in sample or "parent_id" in sample:
                return "comments"
            elif "url" in sample and "text" in sample:
                return "pages"

        return "unknown"

    def _analyze_text_content(self, items: list[JsonItem]) -> None:
        """Analyze text content across all items."""
        items_with_text = 0
        items_with_nontrivial_text = 0
        text_lengths: list[int] = []
        text_lengths_by_type: dict[str, list[int]] = defaultdict(list)
        total_text_length = 0

        for item in items:
            text = self._extract_text(item, TEXT_FIELDS)
            if text:
                items_with_text += 1
                text_len = len(text)
                text_lengths.append(text_len)
                total_text_length += text_len

                if text_len >= MIN_NONTRIVIAL_TEXT_LENGTH:
                    items_with_nontrivial_text += 1

                # track by type
                if "thread_url" in item or "post_id" in item:
                    text_lengths_by_type["posts"].append(text_len)
                elif "url" in item:
                    text_lengths_by_type["pages"].append(text_len)

        if items_with_text > 0:
            self.metrics["items_with_text"] = items_with_text
            self.metrics["items_missing_text"] = len(items) - items_with_text
            self.metrics["non_trivial_text_rate"] = items_with_nontrivial_text / len(items)
            self.metrics["avg_text_length"] = total_text_length / items_with_text
            self.metrics["total_text_chars"] = total_text_length

            for type_name, lengths in text_lengths_by_type.items():
                if lengths:
                    self.metrics[f"avg_{type_name}_text_length"] = sum(lengths) / len(lengths)
                    self.metrics[f"{type_name}_count"] = len(lengths)

            if text_lengths:
                text_lengths.sort()
                self.metrics["min_text_length"] = text_lengths[0]
                self.metrics["max_text_length"] = text_lengths[-1]
                self.metrics["median_text_length"] = text_lengths[len(text_lengths) // 2]

                p25_idx = len(text_lengths) // 4
                p75_idx = (3 * len(text_lengths)) // 4
                self.metrics["text_length_p25"] = text_lengths[p25_idx]
                self.metrics["text_length_p75"] = text_lengths[p75_idx]

    def _analyze_urls(self, items: list[JsonItem]) -> None:
        """Analyze URL patterns across all items."""
        page_urls: set[str] = set()
        thread_urls: set[str] = set()
        all_urls: list[str] = []
        domains: dict[str, int] = defaultdict(int)
        url_patterns: dict[str, int] = defaultdict(int)

        for item in items:
            # track page urls (from pages/raw file)
            if "url" in item and not ("thread_url" in item or "post_id" in item):
                url = item["url"]
                if isinstance(url, str):
                    page_urls.add(url)
                    all_urls.append(url)

            # track thread urls (from posts file)
            if "thread_url" in item and isinstance(item["thread_url"], str):
                thread_url = item["thread_url"]
                thread_urls.add(thread_url)
                all_urls.append(thread_url)

            # analyze all url fields for patterns
            for field in URL_FIELDS:
                if field in item and isinstance(item[field], str):
                    url = item[field]

                    # extract domain and analyze patterns
                    parsed = cast(ParseResult, urlparse(url))
                    if parsed.netloc:
                        domains[parsed.netloc] += 1

                    # analyze url patterns
                    if "/threads/" in url:
                        url_patterns["thread_pattern_count"] += 1
                    if "/post-" in url:
                        url_patterns["post_redirect_count"] += 1
                    if "/page-" in url or "page=" in url:
                        url_patterns["pagination_count"] += 1

        self.metrics["unique_page_urls"] = len(page_urls)
        self.metrics["unique_thread_urls"] = len(thread_urls)

        if all_urls:
            unique_all = set(all_urls)
            self.metrics["total_url_mentions"] = len(all_urls)
            self.metrics["unique_urls_combined"] = len(unique_all)

            if domains:
                self.metrics["unique_domains"] = len(domains)
                top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:3]
                self.metrics["top_domains"] = {domain: count for domain, count in top_domains}

            if url_patterns:
                self.metrics["url_patterns"] = dict(url_patterns)

    def _analyze_identifiers(self, items: list[JsonItem]) -> None:
        """Analyze identifiers and check for duplicates."""
        all_ids: list[str] = []
        for item in items:
            for field in ID_FIELDS:
                if field in item:
                    all_ids.append(str(item[field]))
                    break

        if all_ids:
            unique_ids = set(all_ids)
            self.metrics["items_with_ids"] = len(all_ids)
            self.metrics["unique_ids"] = len(unique_ids)

            if len(all_ids) > len(unique_ids):
                self.metrics["duplicate_items"] = len(all_ids) - len(unique_ids)
                self.metrics["duplication_rate"] = (len(all_ids) - len(unique_ids)) / len(all_ids)

    def _analyze_authors(self, items: list[JsonItem]) -> None:
        """Analyze author/user information."""
        authors: list[str] = []
        for item in items:
            for field in AUTHOR_FIELDS:
                if field in item and item[field]:
                    authors.append(str(item[field]))
                    break

        if authors:
            unique_authors = set(authors)
            self.metrics["items_with_authors"] = len(authors)
            self.metrics["unique_authors"] = len(unique_authors)
            self.metrics["items_per_author"] = len(authors) / len(unique_authors)

            author_counts: dict[str, int] = defaultdict(int)
            for author in authors:
                author_counts[author] += 1

            counts = list(author_counts.values())
            counts.sort(reverse=True)

    def _analyze_threads(self, items: list[JsonItem]) -> None:
        """Analyze thread-related patterns (works for forums, reddit, etc)."""
        thread_ids: list[str] = []

        for item in items:
            thread_id = None

            if "thread_url" in item or "url" in item:
                url = item.get("thread_url") or item.get("url", "")

                for pattern in THREAD_ID_PATTERNS:
                    match = re.search(pattern, url)
                    if match:
                        thread_id = match.group(1)
                        break

            if not thread_id:
                thread_id = item.get("thread_id") or item.get("topic_id")

            if thread_id:
                thread_ids.append(str(thread_id))

        if thread_ids:
            thread_counts: dict[str, int] = defaultdict(int)
            for tid in thread_ids:
                thread_counts[tid] += 1

            self.metrics["unique_threads"] = len(thread_counts)
            self.metrics["total_thread_items"] = len(thread_ids)

            if thread_counts:
                counts: list[int] = list(thread_counts.values())
                counts.sort(reverse=True)

                self.metrics["avg_items_per_thread"] = sum(counts) / len(counts)

                if self.metrics.get("total_items"):
                    self.metrics["thread_coverage_breadth"] = (
                        len(thread_counts) / self.metrics["total_items"]
                    )

    def _analyze_temporal_data(self, items: list[JsonItem]) -> None:
        """Analyze temporal patterns in the data."""
        dates_found = 0
        for item in items:
            for field in DATE_FIELDS:
                if field in item and item[field]:
                    dates_found += 1
                    break

        if dates_found > 0:
            self.metrics["items_with_dates"] = dates_found
            self.metrics["temporal_coverage"] = dates_found / len(items)

    def _extract_text(self, item: JsonItem, field_names: list[str]) -> str:
        """Extract text from item trying multiple field names."""
        for field in field_names:
            if field in item:
                value = item[field]
                if isinstance(value, str) and value.strip():
                    return value
        return ""
