"""Metrics engine for calculating typing metrics."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import statistics

from gdhistogram.analysis.diff_engine import DiffResult
from gdhistogram.config import AnalysisConfig, DEFAULT_CONFIG


@dataclass
class IntervalMetrics:
    """Computed metrics for a single revision interval."""
    
    # Revision info
    from_revision_id: str
    to_revision_id: str
    timestamp: datetime  # End time of interval
    
    # Raw metrics from diff
    chars_inserted: int
    chars_deleted: int
    net_chars: int
    time_delta_seconds: float
    
    # Computed metrics
    words_inserted: float
    wpm: float
    
    # Flags
    is_anomaly: bool = False
    anomaly_reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage/export."""
        return {
            "from_revision_id": self.from_revision_id,
            "to_revision_id": self.to_revision_id,
            "timestamp": self.timestamp.isoformat(),
            "chars_inserted": self.chars_inserted,
            "chars_deleted": self.chars_deleted,
            "net_chars": self.net_chars,
            "time_delta_seconds": self.time_delta_seconds,
            "words_inserted": self.words_inserted,
            "wpm": self.wpm,
            "is_anomaly": self.is_anomaly,
            "anomaly_reason": self.anomaly_reason,
        }


@dataclass
class OverallStatistics:
    """Overall statistics for the entire document analysis."""
    
    total_intervals: int
    valid_intervals: int
    
    # WPM stats
    mean_wpm: float
    median_wpm: float
    std_wpm: float
    max_wpm: float
    min_wpm: float
    
    # Character stats
    total_chars_inserted: int
    total_chars_deleted: int
    total_net_chars: int
    
    # Time stats
    total_time_seconds: float
    first_revision_time: Optional[datetime]
    last_revision_time: Optional[datetime]
    
    # Anomaly counts
    anomaly_count: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        return {
            "total_intervals": self.total_intervals,
            "valid_intervals": self.valid_intervals,
            "mean_wpm": round(self.mean_wpm, 2),
            "median_wpm": round(self.median_wpm, 2),
            "std_wpm": round(self.std_wpm, 2),
            "max_wpm": round(self.max_wpm, 2),
            "min_wpm": round(self.min_wpm, 2),
            "total_chars_inserted": self.total_chars_inserted,
            "total_chars_deleted": self.total_chars_deleted,
            "total_net_chars": self.total_net_chars,
            "total_time_seconds": round(self.total_time_seconds, 2),
            "first_revision_time": self.first_revision_time.isoformat() if self.first_revision_time else None,
            "last_revision_time": self.last_revision_time.isoformat() if self.last_revision_time else None,
            "anomaly_count": self.anomaly_count,
        }


class MetricsEngine:
    """
    Engine for computing typing metrics from diff results.
    
    Calculates WPM, identifies anomalies, and provides statistics.
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the metrics engine.
        
        Args:
            config: Analysis configuration. Uses defaults if not provided.
        """
        self.config = config or DEFAULT_CONFIG
    
    def compute_interval_metrics(self, diff: DiffResult) -> Optional[IntervalMetrics]:
        """
        Compute metrics for a single diff interval.
        
        Args:
            diff: The diff result for this interval.
        
        Returns:
            IntervalMetrics object, or None if the interval is invalid.
        """
        # Skip invalid intervals
        if not diff.is_valid:
            return None
        
        if diff.time_delta_seconds == 0:
            return None
        
        # Calculate words (chars / 5)
        words_inserted = diff.chars_inserted / self.config.chars_per_word
        
        # Calculate WPM
        minutes = diff.time_delta_seconds / 60.0
        wpm = words_inserted / minutes if minutes > 0 else 0
        
        # Check for WPM anomaly
        is_anomaly = False
        anomaly_reason = None
        
        if wpm > self.config.max_valid_wpm:
            is_anomaly = True
            anomaly_reason = f"WPM exceeds maximum ({self.config.max_valid_wpm})"
        
        return IntervalMetrics(
            from_revision_id=diff.from_revision_id,
            to_revision_id=diff.to_revision_id,
            timestamp=diff.to_time,
            chars_inserted=diff.chars_inserted,
            chars_deleted=diff.chars_deleted,
            net_chars=diff.net_chars,
            time_delta_seconds=diff.time_delta_seconds,
            words_inserted=words_inserted,
            wpm=wpm,
            is_anomaly=is_anomaly,
            anomaly_reason=anomaly_reason,
        )
    
    def compute_all_metrics(
        self,
        diffs: List[DiffResult]
    ) -> List[IntervalMetrics]:
        """
        Compute metrics for all diff intervals.
        
        Args:
            diffs: List of diff results.
        
        Returns:
            List of IntervalMetrics objects (invalid intervals excluded).
        """
        metrics: List[IntervalMetrics] = []
        
        for diff in diffs:
            m = self.compute_interval_metrics(diff)
            if m is not None:
                metrics.append(m)
        
        return metrics
    
    def compute_statistics(
        self,
        metrics: List[IntervalMetrics],
        diffs: List[DiffResult]
    ) -> OverallStatistics:
        """
        Compute overall statistics from all interval metrics.
        
        Args:
            metrics: List of computed interval metrics.
            diffs: Original diff results.
        
        Returns:
            OverallStatistics object.
        """
        # Extract valid WPM values (exclude anomalies for stats)
        valid_wpm = [m.wpm for m in metrics if not m.is_anomaly and m.wpm > 0]
        
        # Calculate WPM statistics
        if valid_wpm:
            mean_wpm = statistics.mean(valid_wpm)
            median_wpm = statistics.median(valid_wpm)
            std_wpm = statistics.stdev(valid_wpm) if len(valid_wpm) > 1 else 0.0
            max_wpm = max(valid_wpm)
            min_wpm = min(valid_wpm)
        else:
            mean_wpm = median_wpm = std_wpm = max_wpm = min_wpm = 0.0
        
        # Calculate totals
        total_chars_inserted = sum(m.chars_inserted for m in metrics)
        total_chars_deleted = sum(m.chars_deleted for m in metrics)
        total_net_chars = sum(m.net_chars for m in metrics)
        total_time = sum(m.time_delta_seconds for m in metrics)
        
        # Get time range
        first_time = min((d.from_time for d in diffs), default=None)
        last_time = max((d.to_time for d in diffs), default=None)
        
        # Count anomalies
        anomaly_count = sum(1 for m in metrics if m.is_anomaly)
        
        return OverallStatistics(
            total_intervals=len(diffs),
            valid_intervals=len(metrics),
            mean_wpm=mean_wpm,
            median_wpm=median_wpm,
            std_wpm=std_wpm,
            max_wpm=max_wpm,
            min_wpm=min_wpm,
            total_chars_inserted=total_chars_inserted,
            total_chars_deleted=total_chars_deleted,
            total_net_chars=total_net_chars,
            total_time_seconds=total_time,
            first_revision_time=first_time,
            last_revision_time=last_time,
            anomaly_count=anomaly_count,
        )
    
    def get_wpm_threshold_for_spikes(
        self,
        metrics: List[IntervalMetrics]
    ) -> float:
        """
        Calculate the WPM threshold for spike detection.
        
        Spike threshold = mean + (z_score * std)
        
        Args:
            metrics: List of interval metrics.
        
        Returns:
            WPM threshold above which intervals are considered spikes.
        """
        valid_wpm = [m.wpm for m in metrics if not m.is_anomaly and m.wpm > 0]
        
        if len(valid_wpm) < 2:
            return float('inf')
        
        mean_wpm = statistics.mean(valid_wpm)
        std_wpm = statistics.stdev(valid_wpm)
        
        return mean_wpm + (self.config.spike_z_score_threshold * std_wpm)
