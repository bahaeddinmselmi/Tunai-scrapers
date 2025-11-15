import time

import psutil
from pydantic import BaseModel

BYTES_PER_KB = 1024
BYTES_PER_MB = BYTES_PER_KB * BYTES_PER_KB
TIMESTAMP_FORMAT_HUMAN = "%Y-%m-%d %H:%M:%S"


class BenchmarkMetrics(BaseModel):
    total_runtime_seconds: float
    items_extracted: int
    items_per_second: float
    peak_memory_mb: float
    avg_cpu_percent: float
    success: bool

    collector_name: str
    scenario_name: str
    timestamp: str
    log_file: str = ""


class MetricsCollector:
    """Collect metrics during scraper execution."""

    def __init__(self, collector_name: str, scenario_name: str) -> None:
        self.collector_name: str = collector_name
        self.scenario_name: str = scenario_name
        self.log_file: str = ""
        self._start_time: float | None = None
        self._target_process: psutil.Process | None = None
        self._peak_memory: float = 0.0
        self._cpu_samples: list[float] = []

    def start(self) -> None:
        """Start collecting metrics."""
        self._start_time = time.time()

    def attach_to_process(self, process_id: int) -> None:
        """Attach to subprocess for monitoring."""
        try:
            self._target_process = psutil.Process(process_id)
            _ = self._target_process.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def sample(self) -> None:
        """Sample resource usage."""
        if self._target_process is None:
            return

        try:
            rss: int = int(self._target_process.memory_info().rss)  # pyright: ignore[reportAny]
            memory_mb: float = float(rss / BYTES_PER_MB)

            try:
                for child in self._target_process.children(recursive=True):
                    try:
                        child_rss: int = int(child.memory_info().rss)  # pyright: ignore[reportAny]
                        memory_mb += float(child_rss / BYTES_PER_MB)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            self._peak_memory = max(self._peak_memory, memory_mb)

            cpu = self._target_process.cpu_percent(None)
            if cpu and cpu > 0:
                self._cpu_samples.append(cpu)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def stop(self, items_count: int, success: bool) -> BenchmarkMetrics:
        """Stop metrics collection and return results."""
        if self._start_time is None:
            raise RuntimeError("Metrics never started")

        runtime = time.time() - self._start_time

        return BenchmarkMetrics(
            total_runtime_seconds=runtime,
            items_extracted=items_count,
            items_per_second=items_count / runtime if runtime > 0 else 0.0,
            peak_memory_mb=self._peak_memory,
            avg_cpu_percent=sum(self._cpu_samples) / len(self._cpu_samples)
            if self._cpu_samples
            else 0.0,
            success=success,
            collector_name=self.collector_name,
            scenario_name=self.scenario_name,
            timestamp=time.strftime(TIMESTAMP_FORMAT_HUMAN),
            log_file=self.log_file,
        )
