"""Benchmark runner for scrapers with quality metrics."""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .enhanced_metrics import EnhancedMetricsAnalyzer
from .metrics import MetricsCollector
from .quality_metrics import MetricsAnalyzer

CACHE_DIR_DEFAULT = Path.home() / ".cache" / "tunai_scrapers"
BENCHMARK_RESULTS_DIR_DEFAULT = CACHE_DIR_DEFAULT / "benchmarks" / "results"
BENCHMARK_LOGS_DIR_DEFAULT = CACHE_DIR_DEFAULT / "benchmarks" / "logs"
BENCHMARK_DATA_DIR_DEFAULT = CACHE_DIR_DEFAULT / "benchmarks" / "data"

ENV_VAR_RESULTS_DIR = "TUNAI_PARSER_BENCHMARK_RESULTS"
ENV_VAR_LOGS_DIR = "TUNAI_PARSER_BENCHMARK_LOGS"
ENV_VAR_DATA_DIR = "TUNAI_PARSER_BENCHMARK_DATA"

BENCHMARK_TIMEOUT_SECONDS_DEFAULT = 300
BENCHMARK_COLLECTOR_LIMIT_DEFAULT = 50
RESOURCE_SAMPLE_INTERVAL_SECONDS = 0.5

BYTES_PER_KB = 1024
BYTES_PER_MB = BYTES_PER_KB * BYTES_PER_KB

JSON_INDENT_SPACES = 2

TIMESTAMP_FORMAT_FILE = "%Y%m%d_%H%M%S"
TIMESTAMP_FORMAT_HUMAN = "%Y-%m-%d %H:%M:%S"

ERROR_LOG_TAIL_LINES = 30


class BenchmarkRunner:
    """Manages benchmark execution and metrics collection."""

    def __init__(self, local: bool = False):
        """Initialize benchmark runner.

        Args:
            local: If True, save results in local directory instead of cache.
        """
        self.local = local
        self._setup_directories()

    def _setup_directories(self) -> None:
        """Setup benchmark directories based on local flag."""
        if self.local:
            base_dir = Path(__file__).parent
            self.results_dir = base_dir / "results"
            self.logs_dir = base_dir / "logs"
            self.data_dir = base_dir / "data"
        else:
            self.results_dir = self._get_env_dir(ENV_VAR_RESULTS_DIR, BENCHMARK_RESULTS_DIR_DEFAULT)
            self.logs_dir = self._get_env_dir(ENV_VAR_LOGS_DIR, BENCHMARK_LOGS_DIR_DEFAULT)
            self.data_dir = self._get_env_dir(ENV_VAR_DATA_DIR, BENCHMARK_DATA_DIR_DEFAULT)

        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_env_dir(env_var: str, default: Path) -> Path:
        """Get directory from environment variable or use default."""
        env_path = os.getenv(env_var)
        return Path(env_path) if env_path else default

    def run_benchmark(
        self,
        collector_name: str,
        limit: int,
        delete_data: bool = False,
    ) -> dict[str, Any]:
        """Run a benchmark for a specific collector.

        Args:
            collector_name: Name of the collector to benchmark.
            limit: Limit parameter for the collector.
            delete_data: Whether to delete collected data after benchmark.

        Returns:
            Dictionary containing benchmark results and metrics.
        """
        timestamp = time.strftime(TIMESTAMP_FORMAT_FILE)
        run_data_dir = self.data_dir / f"{collector_name}_{limit}_{timestamp}"
        run_data_dir.mkdir(parents=True, exist_ok=True)

        collector_config = self._get_collector_config(collector_name, limit, run_data_dir)

        result = self._execute_benchmark(
            command=collector_config["command"],
            output_files=collector_config["output_files"],
            collector_name=collector_name,
            scenario_name=str(limit),
        )

        if delete_data:
            shutil.rmtree(run_data_dir, ignore_errors=True)

        return result

    def _get_collector_config(
        self, collector_name: str, limit: int, run_data_dir: Path
    ) -> dict[str, Any]:
        """Get configuration for a specific collector."""
        project_root = Path(__file__).parent.parent
        collectors_dir = project_root / "collectors"

        if collector_name == "reddit":
            return self._config_reddit(limit, run_data_dir, collectors_dir)
        elif collector_name == "sites":
            return self._config_sites(limit, run_data_dir, collectors_dir)
        elif collector_name == "tunisia_sat":
            return self._config_tunisia_sat(limit, run_data_dir, collectors_dir)
        elif collector_name == "derja_ninja":
            return self._config_derja_ninja(limit, run_data_dir, collectors_dir)
        elif collector_name == "youtube":
            return self._config_youtube(limit, run_data_dir, collectors_dir)
        elif collector_name == "facebook":
            return self._config_facebook(limit, run_data_dir, collectors_dir)
        elif collector_name.startswith("scrapy_"):
            return self._config_scrapy(collector_name, limit, run_data_dir)
        else:
            raise ValueError(f"Unknown collector '{collector_name}'")

    def _config_reddit(
        self, limit: int, run_data_dir: Path, collectors_dir: Path
    ) -> dict[str, Any]:
        """Configure reddit collector."""
        out_posts = run_data_dir / "posts.jsonl"
        out_comments = run_data_dir / "comments.jsonl"

        return {
            "command": [
                sys.executable,
                str(collectors_dir / "collect_reddit.py"),
                "--sub",
                "Tunisia",
                "--limit",
                str(limit),
                "--sort",
                "new",
                "--out_posts",
                str(out_posts),
                "--out_comments",
                str(out_comments),
            ],
            "output_files": [out_posts, out_comments],
        }

    def _config_sites(self, limit: int, run_data_dir: Path, collectors_dir: Path) -> dict[str, Any]:
        """Configure sites collector."""
        out_file = run_data_dir / "sites.jsonl"

        return {
            "command": [
                sys.executable,
                str(collectors_dir / "collect_sites.py"),
                "--start_urls",
                "https://www.pm.gov.tn",
                "--domains",
                "pm.gov.tn",
                "--max_pages",
                str(limit),
                "--out",
                str(out_file),
            ],
            "output_files": [out_file],
        }

    def _config_tunisia_sat(
        self, limit: int, run_data_dir: Path, collectors_dir: Path
    ) -> dict[str, Any]:
        """Configure tunisia_sat collector."""
        out_raw = run_data_dir / "raw.jsonl"
        out_posts = run_data_dir / "posts.jsonl"
        out_vocab = run_data_dir / "vocab.json"

        return {
            "command": [
                sys.executable,
                str(collectors_dir / "collect_tunisia_sat.py"),
                "--max_pages",
                str(limit),
                "--out_vocab",
                str(out_vocab),
                "--out_raw",
                str(out_raw),
                "--out_posts",
                str(out_posts),
            ],
            "output_files": [out_raw, out_posts, out_vocab],
        }

    def _config_derja_ninja(
        self, limit: int, run_data_dir: Path, collectors_dir: Path
    ) -> dict[str, Any]:
        """Configure derja_ninja collector."""
        out_raw = run_data_dir / "pages.jsonl"
        out_cards = run_data_dir / "cards.jsonl"
        out_vocab = run_data_dir / "vocab.json"

        return {
            "command": [
                sys.executable,
                str(collectors_dir / "collect_derja_ninja.py"),
                "--max_pages",
                str(limit),
                "--out_vocab",
                str(out_vocab),
                "--out_raw",
                str(out_raw),
                "--out_cards",
                str(out_cards),
            ],
            "output_files": [out_raw, out_cards, out_vocab],
        }

    def _config_youtube(
        self, limit: int, run_data_dir: Path, collectors_dir: Path
    ) -> dict[str, Any]:
        """Configure youtube collector."""
        out_file = run_data_dir / "youtube.jsonl"

        return {
            "command": [
                "uv",
                "run",
                "python",
                str(collectors_dir / "collect_youtube.py"),
                "--search",
                "darija tunisienne",
                "--pages",
                str(limit),
                "--out",
                str(out_file),
            ],
            "output_files": [out_file],
        }

    def _config_facebook(
        self, limit: int, run_data_dir: Path, collectors_dir: Path
    ) -> dict[str, Any]:
        """Configure facebook group collector.

        `limit` is interpreted as per_group_limit to match other collectors
        where the limit parameter controls the primary quantity of interest.
        """
        out_file = run_data_dir / "facebook_groups.jsonl"

        return {
            "command": [
                sys.executable,
                str(collectors_dir / "collect_facebook.py"),
                "--groups",
                "Texas A&M Free and For Sale",
                "--per_group_limit",
                str(limit),
                "--out",
                str(out_file),
            ],
            "output_files": [out_file],
        }

    def _config_scrapy(self, collector_name: str, limit: int, run_data_dir: Path) -> dict[str, Any]:
        """Configure scrapy collectors."""
        spider_name = collector_name.removeprefix("scrapy_")
        out_dir = run_data_dir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            "uv",
            "run",
            "scrapy",
            "crawl",
            spider_name,
            "-s",
            f"OUTPUT_DIR={out_dir}",
            "-s",
            "LOG_LEVEL=INFO",
        ]

        if spider_name == "reddit":
            cmd.extend(["-a", f"limit={limit}", "-a", "sub=Tunisia"])
            output_files = [out_dir / "reddit_posts.jsonl"]
        elif spider_name == "sites":
            cmd.extend(
                [
                    "-a",
                    f"max_pages={limit}",
                    "-a",
                    "start_urls=https://www.pm.gov.tn",
                    "-a",
                    "domains=pm.gov.tn",
                ]
            )
            output_files = [out_dir / "sites.jsonl"]
        elif spider_name == "tunisia_sat":
            cmd.extend(["-a", f"max_pages={limit}"])
            output_files = [
                out_dir / "tunisia_sat_posts.jsonl",
                out_dir / "tunisia_sat_pages.jsonl",
                out_dir.parent / "processed" / "tunisia_sat_words.json",
            ]
        elif spider_name == "derja_ninja":
            cmd.extend(["-a", f"max_pages={limit}"])
            output_files = [
                out_dir / "derja_ninja_pages.jsonl",
                out_dir / "derja_ninja_cards.jsonl",
                out_dir.parent / "processed" / "derja_ninja_words.json",
            ]
        elif spider_name == "youtube":
            cmd.extend(
                [
                    "-a",
                    f"pages={limit}",
                    "-a",
                    "search=darija tunisienne",
                ]
            )
            output_files = [out_dir / "youtube.jsonl"]
        elif spider_name == "facebook_groups":
            cmd.extend(
                [
                    "-a",
                    "groups=Texas A&M Free and For Sale",
                    "-a",
                    f"per_group_limit={limit}",
                ]
            )
            output_files = [out_dir / "facebook_groups.jsonl"]
        else:
            raise ValueError(f"Unknown scrapy spider '{spider_name}'")

        return {"command": cmd, "output_files": output_files}

    def _execute_benchmark(
        self,
        command: list[str],
        output_files: list[Path],
        collector_name: str,
        scenario_name: str,
        timeout_seconds: int = BENCHMARK_TIMEOUT_SECONDS_DEFAULT,
    ) -> dict[str, Any]:
        """Execute benchmark and collect metrics."""
        timestamp = time.strftime(TIMESTAMP_FORMAT_FILE)
        log_file = self.logs_dir / f"{collector_name}_{timestamp}.log"

        metrics = MetricsCollector(collector_name, scenario_name)
        metrics.log_file = str(log_file)
        metrics.start()

        exit_code = self._run_process(command, log_file, metrics, timeout_seconds)

        items_count = sum(self._count_items_in_jsonl(f) for f in output_files if f.exists())
        success = exit_code == 0

        result = metrics.stop(items_count, success)
        result_dict = result.model_dump()

        if success:
            result_dict = self._add_quality_metrics(
                result_dict, output_files, result.total_runtime_seconds
            )
            self._print_success_summary(result, result_dict)
        else:
            self._print_error_summary(collector_name, exit_code, log_file)

        self._save_results(result_dict, collector_name, timestamp)

        print(f"[RESULTS] {self.results_dir / f'{collector_name}_{timestamp}.json'}")
        print(f"[LOG] {log_file}")
        self._print_data_files(output_files)

        return result_dict

    def _run_process(
        self,
        command: list[str],
        log_file: Path,
        metrics: MetricsCollector,
        timeout_seconds: int,
    ) -> int:
        """Run the collector process with monitoring."""
        with open(log_file, "w", encoding="utf-8") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, text=True)
            metrics.attach_to_process(process.pid)

            start_time = time.time()
            while True:
                exit_code = process.poll()
                if exit_code is not None:
                    return exit_code

                if time.time() - start_time > timeout_seconds:
                    process.kill()
                    process.wait()
                    return -1

                metrics.sample()
                time.sleep(RESOURCE_SAMPLE_INTERVAL_SECONDS)

    def _add_quality_metrics(
        self,
        result_dict: dict[str, Any],
        output_files: list[Path],
        runtime_seconds: float,
    ) -> dict[str, Any]:
        """Add quality metrics to results."""
        analyzer = MetricsAnalyzer(output_files)
        quality_metrics = analyzer.calculate_all_metrics()
        result_dict.update(quality_metrics)

        # Add enhanced metrics for duplication analysis
        if output_files:
            try:
                enhanced = EnhancedMetricsAnalyzer()
                items = []
                for file_path in output_files:
                    if file_path.suffix == ".jsonl" and "posts" in file_path.name:
                        with open(file_path) as f:
                            for line in f:
                                try:
                                    items.append(json.loads(line))
                                except json.JSONDecodeError:
                                    continue

                if items:
                    result_dict["enhanced_metrics"] = enhanced.calculate_all_metrics(items)
            except Exception as e:
                result_dict["enhanced_metrics_error"] = str(e)

        if runtime_seconds > 0:
            total_items = quality_metrics.get("total_items", 0)
            if total_items > 0:
                result_dict["items_per_second"] = total_items / runtime_seconds

            items_with_text = quality_metrics.get("items_with_text", 0)
            if items_with_text > 0:
                result_dict["text_items_per_second"] = items_with_text / runtime_seconds

        return result_dict

    def _print_success_summary(self, result: Any, metrics: dict[str, Any]) -> None:
        """Print summary for successful benchmark."""
        print(
            f"\n[COMPLETE] Runtime: {result.total_runtime_seconds:.1f}s | "
            f"Items: {result.items_extracted} | "
            f"Memory: {result.peak_memory_mb:.1f}MB"
        )

        # Print enhanced metrics if available
        if "enhanced_metrics" in metrics:
            em = metrics["enhanced_metrics"]

            # Duplication metrics
            if "duplication" in em:
                dup = em["duplication"]
                print("\n[DUPLICATION METRICS]")
                print(f"  Duplication rate: {dup['duplication_rate']:.1%}")
                print(f"  Unique content: {dup['unique_content_hashes']} items")
                print(f"  Unique post IDs: {dup['unique_post_ids']}")
                if dup.get("max_duplications", 0) > 1:
                    print(f"  Max duplications: {dup['max_duplications']}x")

            # Author coverage metrics
            if "authors" in em:
                auth = em["authors"]
                print("\n[AUTHOR METRICS]")
                print(f"  Author coverage: {auth['author_coverage_rate']:.1%}")
                print(f"  Unique authors: {auth['unique_authors']}")
                total_posts = auth["posts_with_authors"] + auth["posts_without_authors"]
                print(f"  Posts with authors: {auth['posts_with_authors']}/{total_posts}")

            # Crawl behavior metrics
            if "crawl" in em:
                crawl = em["crawl"]
                print("\n[CRAWL METRICS]")
                print(f"  Unique threads: {crawl['unique_threads']}")
                print(f"  Avg thread depth: {crawl['avg_thread_depth']:.1f} posts/thread")
                print(f"  Max thread depth: {crawl['max_thread_depth']} posts")

        quality_keys = [
            ("items_per_second", "Items/sec", "{:.2f}"),
            ("unique_page_urls", "Unique page URLs", "{}"),
            ("unique_thread_urls", "Unique thread URLs", "{}"),
            ("unique_threads", "Unique threads", "{}"),
            ("avg_items_per_thread", "Avg items/thread", "{:.1f}"),
            ("unique_authors", "Unique authors", "{}"),
            ("avg_text_length", "Avg text length", "{:.0f} chars"),
            ("non_trivial_text_rate", "Non-trivial text", "{:.1%}"),
        ]

        quality_metrics = [(k, n, f) for k, n, f in quality_keys if k in metrics]
        if quality_metrics:
            print("[QUALITY METRICS]")
            for key, name, fmt in quality_metrics:
                print(f"  {name}: {fmt.format(metrics[key])}")

    def _print_error_summary(self, collector_name: str, exit_code: int, log_file: Path) -> None:
        """Print summary for failed benchmark."""
        print(f"\n[ERROR] Collector '{collector_name}' failed with exit code {exit_code}")
        print(f"[ERROR] See log: {log_file}")
        self._print_error_log_tail(log_file)

    def _save_results(
        self, result_dict: dict[str, Any], collector_name: str, timestamp: str
    ) -> None:
        """Save benchmark results to JSON file."""
        result_file = self.results_dir / f"{collector_name}_{timestamp}.json"
        with open(result_file, "w", encoding="utf-8") as file:
            json.dump(result_dict, file, indent=JSON_INDENT_SPACES, default=str)

    @staticmethod
    def _count_items_in_jsonl(filepath: Path) -> int:
        """Count items in a JSONL file."""
        try:
            with open(filepath, encoding="utf-8") as file:
                return sum(1 for _ in file)
        except Exception:
            return 0

    @staticmethod
    def _print_data_files(output_files: list[Path]) -> None:
        """Print information about output data files."""
        existing_files = [f for f in output_files if f.exists()]
        if not existing_files:
            return

        print("[DATA]")
        for path in existing_files:
            count = BenchmarkRunner._count_items_in_jsonl(path)
            print(f"  {path} ({count} items)")

    @staticmethod
    def _print_error_log_tail(log_file: Path) -> None:
        """Print the last few lines of error log."""
        try:
            with open(log_file, encoding="utf-8") as file:
                lines = file.readlines()
        except Exception:
            return

        if not lines:
            return

        print("[ERROR] Log tail:")
        print("".join(lines[-ERROR_LOG_TAIL_LINES:]))


def main() -> None:
    """CLI entry point for benchmark runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark scrapers with quality metrics")
    parser.add_argument(
        "--collector",
        required=True,
        choices=[
            "reddit",
            "sites",
            "tunisia_sat",
            "derja_ninja",
            "youtube",
            "facebook",
            "scrapy_reddit",
            "scrapy_sites",
            "scrapy_tunisia_sat",
            "scrapy_derja_ninja",
            "scrapy_youtube",
            "scrapy_facebook_groups",
        ],
        help="Collector to benchmark",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=BENCHMARK_COLLECTOR_LIMIT_DEFAULT,
        help=(
            "Limit for collector (posts for reddit, per-group posts for facebook, "
            "pages for sites/tunisia_sat)"
        ),
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Save results/logs under benchmarks/ instead of cache directory",
    )
    parser.add_argument(
        "--delete-data",
        action="store_true",
        help="Delete scraped data after benchmark (default is to keep it)",
    )
    args = parser.parse_args()

    if "reddit" in args.collector:
        item_type = "posts"
    elif "youtube" in args.collector:
        item_type = "pages (videos)"
    elif "facebook" in args.collector:
        item_type = "posts per group"
    else:
        item_type = "pages"
    print(f"\n[BENCHMARK] Starting {args.collector} with {args.limit} {item_type}")

    runner = BenchmarkRunner(local=args.local)
    runner.run_benchmark(
        collector_name=args.collector,
        limit=args.limit,
        delete_data=args.delete_data,
    )


if __name__ == "__main__":
    main()
