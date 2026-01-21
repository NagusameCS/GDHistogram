"""Analysis module for GDHistogram."""

from gdhistogram.analysis.diff_engine import DiffEngine, DiffResult
from gdhistogram.analysis.metrics_engine import MetricsEngine, IntervalMetrics
from gdhistogram.analysis.event_detector import EventDetector, DetectedEvent, EventType

__all__ = [
    "DiffEngine",
    "DiffResult", 
    "MetricsEngine",
    "IntervalMetrics",
    "EventDetector",
    "DetectedEvent",
    "EventType",
]
