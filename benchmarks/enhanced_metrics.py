"""Enhanced metrics for comprehensive benchmark analysis."""

import hashlib
from collections import Counter, defaultdict
from typing import Any


class EnhancedMetricsAnalyzer:
    """Analyzes collected data with enhanced metrics including duplication detection."""

    def analyze_duplication(self, items: list[dict]) -> dict[str, Any]:
        """Analyze content duplication in collected items.

        Args:
            items: List of collected items

        Returns:
            Dictionary with duplication metrics
        """
        post_ids = []
        content_hashes = []
        duplicate_count = 0
        unique_posts = set()
        posts_by_id = defaultdict(list)

        for item in items:
            # Get post ID if available
            post_id = item.get("post_id") or item.get("id")
            if post_id:
                post_ids.append(post_id)
                posts_by_id[post_id].append(item)

            # Create content hash for deduplication
            text = item.get("text", "")
            if text:
                content_hash = hashlib.md5(text.encode()).hexdigest()
                if content_hash in unique_posts:
                    duplicate_count += 1
                else:
                    unique_posts.add(content_hash)
                content_hashes.append(content_hash)

        # Calculate duplication metrics
        total_posts = len(post_ids)
        unique_post_ids = len(set(post_ids))
        unique_content = len(unique_posts)

        # Find posts that appear multiple times
        duplicate_ids = {pid: count for pid, count in Counter(post_ids).items() if count > 1}

        return {
            "total_posts": total_posts,
            "unique_post_ids": unique_post_ids,
            "unique_content_hashes": unique_content,
            "duplicate_count": duplicate_count,
            "duplication_rate": duplicate_count / total_posts if total_posts > 0 else 0,
            "id_duplication_rate": (total_posts - unique_post_ids) / total_posts
            if total_posts > 0
            else 0,
            "content_duplication_rate": (total_posts - unique_content) / total_posts
            if total_posts > 0
            else 0,
            "duplicate_id_count": len(duplicate_ids),
            "max_duplications": max(Counter(post_ids).values()) if post_ids else 0,
        }

    def analyze_author_coverage(self, items: list[dict]) -> dict[str, Any]:
        """Analyze author extraction coverage.

        Args:
            items: List of collected items

        Returns:
            Dictionary with author coverage metrics
        """
        posts_with_authors = 0
        unique_authors = set()
        null_authors = 0
        author_post_counts = Counter()

        for item in items:
            author = item.get("author")
            if author is not None:
                posts_with_authors += 1
                unique_authors.add(author)
                author_post_counts[author] += 1
            else:
                null_authors += 1

        total = len(items)

        return {
            "posts_with_authors": posts_with_authors,
            "posts_without_authors": null_authors,
            "author_coverage_rate": posts_with_authors / total if total > 0 else 0,
            "unique_authors": len(unique_authors),
            "avg_posts_per_author": posts_with_authors / len(unique_authors)
            if unique_authors
            else 0,
        }

    def analyze_crawl_behavior(self, items: list[dict]) -> dict[str, Any]:
        """Analyze crawl behavior and strategy.

        Args:
            items: List of collected items

        Returns:
            Dictionary with crawl behavior metrics
        """
        threads = defaultdict(list)
        pages = set()

        for item in items:
            # Track threads
            thread_url = item.get("thread_url") or item.get("url", "")
            if "/threads/" in thread_url:
                thread_id = thread_url.split("/threads/")[1].split("/")[0]
                threads[thread_id].append(item)

            # Track pages
            url = item.get("url", "")
            if url:
                pages.add(url)

        thread_depths = [len(posts) for posts in threads.values()]

        return {
            "unique_threads": len(threads),
            "unique_pages": len(pages),
            "avg_thread_depth": sum(thread_depths) / len(thread_depths) if thread_depths else 0,
            "min_thread_depth": min(thread_depths) if thread_depths else 0,
            "max_thread_depth": max(thread_depths) if thread_depths else 0,
        }

    def calculate_all_metrics(self, items: list[dict]) -> dict[str, Any]:
        """Calculate all enhanced metrics for a set of items.

        Args:
            items: List of collected items

        Returns:
            Dictionary with all metrics
        """
        if not items:
            return {}

        return {
            "duplication": self.analyze_duplication(items),
            "authors": self.analyze_author_coverage(items),
            "crawl": self.analyze_crawl_behavior(items),
        }
