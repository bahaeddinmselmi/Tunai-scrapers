"""Pipeline mixins for reducing code duplication."""

import json
from pathlib import Path
from typing import Any

from tunai_scrapers.utils.text import build_vocab


class VocabularyPipelineMixin:
    """Mixin for pipelines that need to save vocabulary data.

    Usage:
        class MyPipeline(VocabularyPipelineMixin, JsonLinesWriter):
            def close_spider(self, spider):
                super().close_spider(spider)
                self.save_vocabulary(spider, "site_name")
    """

    def save_vocabulary(self, spider, site_name: str, vocab_filename: str | None = None) -> None:
        """Save vocabulary data from spider.

        Args:
            spider: Spider instance with freq and samples attributes
            site_name: Name of the site for the vocab data
            vocab_filename: Optional custom filename (defaults to {spider.name}_words.json)
        """
        if not hasattr(spider, "freq") or not spider.freq:
            return

        # Get output directory from spider or pipeline
        output_dir = getattr(self, "output_dir", Path("data"))
        processed_dir = output_dir.parent / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Build vocab data
        vocab = build_vocab(spider.freq, spider.samples)
        vocab_data = {
            "site": site_name,
            "total_words": len(vocab),
            "vocab": vocab,
        }

        # Save to file
        if vocab_filename is None:
            vocab_filename = f"{spider.name}_words.json"
        vocab_file = processed_dir / vocab_filename

        with open(vocab_file, "w", encoding="utf-8") as f:
            json.dump(vocab_data, f, ensure_ascii=False, indent=2)


class MultiFilePipelineMixin:
    """Mixin for pipelines that write to multiple files.

    Provides helpers for managing multiple output files.
    """

    def open_multiple_files(self, base_dir: Path, file_specs: dict[str, str]) -> dict[str, Any]:
        """Open multiple files for writing.

        Args:
            base_dir: Base directory for files
            file_specs: Dictionary mapping file key to filename

        Returns:
            Dictionary of file handles
        """
        base_dir.mkdir(parents=True, exist_ok=True)
        files = {}

        for key, filename in file_specs.items():
            files[key] = open(base_dir / filename, "w", encoding="utf-8")

        return files

    def close_multiple_files(self, files: dict[str, Any]) -> None:
        """Close multiple file handles.

        Args:
            files: Dictionary of file handles to close
        """
        for f in files.values():
            if hasattr(f, "close"):
                f.close()

    def write_jsonl(self, file_handle: Any, item: Any) -> None:
        """Write item as JSON line.

        Args:
            file_handle: File handle to write to
            item: Item to write as JSON (dict or Scrapy Item)
        """
        # Convert to dict if it's a Scrapy Item
        item_dict = dict(item) if hasattr(item, "__getitem__") else item
        line = json.dumps(item_dict, ensure_ascii=False) + "\n"
        file_handle.write(line)
