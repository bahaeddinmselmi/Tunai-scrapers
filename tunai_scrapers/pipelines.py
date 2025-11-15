"""Pipelines for processing scraped items."""

import json
from pathlib import Path
from typing import Any

from tunai_scrapers.pipeline_mixins import MultiFilePipelineMixin, VocabularyPipelineMixin


class JsonLinesWriter:
    """Base class for writing items to JSONL files."""

    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.files: dict[str, Any] = {}

    @classmethod
    def from_crawler(cls, crawler):
        output_dir = crawler.settings.get("OUTPUT_DIR", "data/raw")
        return cls(output_dir)

    def open_spider(self, spider):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.get_output_file(spider)
        self.files[spider.name] = open(output_file, "w", encoding="utf-8")

    def close_spider(self, spider):
        if spider.name in self.files:
            self.files[spider.name].close()

    def transform_item(self, item, spider):
        """Hook for transforming items before writing."""
        return item

    def process_item(self, item, spider):
        transformed = self.transform_item(item, spider)
        if transformed is None:
            return item

        if spider.name in self.files:
            line = json.dumps(dict(transformed), ensure_ascii=False) + "\n"
            self.files[spider.name].write(line)
        return transformed

    def get_output_file(self, spider) -> Path:
        return self.output_dir / f"{spider.name}.jsonl"


class RedditPipeline(MultiFilePipelineMixin, JsonLinesWriter):
    """Separate posts and comments into different files."""

    def open_spider(self, spider):
        self.output_dir.mkdir(parents=True, exist_ok=True)

        file_specs = {"posts": "reddit_posts.jsonl"}
        if getattr(spider, "with_comments", False):
            file_specs["comments"] = "reddit_comments.jsonl"

        self.files = self.open_multiple_files(self.output_dir, file_specs)

    def close_spider(self, spider):
        self.close_multiple_files(self.files)

    def process_item(self, item, spider):
        transformed = self.transform_item(item, spider)
        if transformed is None:
            return item

        source = transformed.get("source", "")
        if source == "reddit_comment" and "comments" in self.files:
            self.write_jsonl(self.files["comments"], transformed)
        else:
            self.write_jsonl(self.files["posts"], transformed)
        return transformed


class TunisiaSatPipeline(VocabularyPipelineMixin, MultiFilePipelineMixin, JsonLinesWriter):
    """Handle posts, pages, and vocabulary for Tunisia-sat."""

    def open_spider(self, spider):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir.parent / "processed").mkdir(parents=True, exist_ok=True)

        self.files = self.open_multiple_files(
            self.output_dir,
            {
                "posts": "tunisia_sat_posts.jsonl",
                "pages": "tunisia_sat_pages.jsonl",
            },
        )

    def close_spider(self, spider):
        self.close_multiple_files(self.files)
        self.save_vocabulary(spider, "tunisia-sat.com", "tunisia_sat_words.json")

    def process_item(self, item, spider):
        transformed = self.transform_item(item, spider)
        if transformed is None:
            return item

        if transformed.get("source") == "tunisia-sat":
            self.write_jsonl(self.files["posts"], transformed)
        else:
            self.write_jsonl(self.files["pages"], transformed)
        return transformed


class DerjaNinjaPipeline(VocabularyPipelineMixin, MultiFilePipelineMixin, JsonLinesWriter):
    """Handle pages, cards, and vocabulary for Derja Ninja."""

    def open_spider(self, spider):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir.parent / "processed").mkdir(parents=True, exist_ok=True)

        self.files = self.open_multiple_files(
            self.output_dir,
            {
                "pages": "derja_ninja_pages.jsonl",
                "cards": "derja_ninja_cards.jsonl",
            },
        )

    def close_spider(self, spider):
        self.close_multiple_files(self.files)
        self.save_vocabulary(spider, "derja.ninja", "derja_ninja_words.json")

    def process_item(self, item, spider):
        transformed = self.transform_item(item, spider)
        if transformed is None:
            return item

        if "english" in transformed:
            self.write_jsonl(self.files["cards"], transformed)
        else:
            self.write_jsonl(self.files["pages"], transformed)
        return transformed


class BettounsiPipeline(VocabularyPipelineMixin, JsonLinesWriter):
    """Handle pages and vocabulary for Bettounsi."""

    def open_spider(self, spider):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir.parent / "processed").mkdir(parents=True, exist_ok=True)

        self.files["pages"] = open(self.output_dir / "bettounsi_pages.jsonl", "w", encoding="utf-8")

    def close_spider(self, spider):
        for f in self.files.values():
            f.close()

        # For Bettounsi, spider already has vocab_data prepared
        if hasattr(spider, "vocab_data"):
            vocab_file = self.output_dir.parent / "processed" / "bettounsi_words.json"
            with open(vocab_file, "w", encoding="utf-8") as f:
                json.dump(spider.vocab_data, f, ensure_ascii=False, indent=2)

    def process_item(self, item, spider):
        transformed = self.transform_item(item, spider)
        if transformed is None:
            return item

        line = json.dumps(dict(transformed), ensure_ascii=False) + "\n"
        self.files["pages"].write(line)
        return transformed
