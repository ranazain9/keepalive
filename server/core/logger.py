"""
KeepAlive Core Telemetry & Latency Logger
Tracks millisecond-level timestamps for life-critical performance verification.
"""

import time
import logging
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger("KeepAlive")

class LatencyTracker:
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
        self.elapsed_ms: float = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0
            logger.info(f"⚡ [{self.operation_name}] Execution time: {self.elapsed_ms:.2f} ms")
