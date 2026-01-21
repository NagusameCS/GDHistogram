"""Event detector for identifying anomalies in typing patterns."""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from gdhistogram.analysis.diff_engine import DiffResult, DiffEngine
from gdhistogram.analysis.metrics_engine import IntervalMetrics, MetricsEngine
from gdhistogram.config import AnalysisConfig, DEFAULT_CONFIG


class EventType(Enum):
    """Types of detected events."""
    COPY_PASTE = "copy_paste"
    SPIKE = "spike"
    IDLE_BURST = "idle_burst"


@dataclass
class DetectedEvent:
    """A detected anomaly event."""
    
    event_type: EventType
    revision_id: str
    timestamp: datetime
    
    # Event details
    wpm: float
    chars_inserted: int
    time_delta_seconds: float
    
    # Confidence/reason
    reason: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage/export."""
        return {
            "event_type": self.event_type.value,
            "revision_id": self.revision_id,
            "timestamp": self.timestamp.isoformat(),
            "wpm": round(self.wpm, 2),
            "chars_inserted": self.chars_inserted,
            "time_delta_seconds": round(self.time_delta_seconds, 2),
            "reason": self.reason,
        }
    
    @property
    def display_name(self) -> str:
        """Get display name for the event type."""
        names = {
            EventType.COPY_PASTE: "Copy/Paste",
            EventType.SPIKE: "Speed Spike",
            EventType.IDLE_BURST: "Idle Burst",
        }
        return names.get(self.event_type, str(self.event_type))


class EventDetector:
    """
    Detector for anomalous events in typing patterns.
    
    Detects:
    - Copy/Paste events (large insertions in short time, low overlap)
    - Speed spikes (WPM significantly above average)
    - Idle bursts (long pause followed by burst of activity)
    
    All detection rules are deterministic and configurable.
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the event detector.
        
        Args:
            config: Analysis configuration. Uses defaults if not provided.
        """
        self.config = config or DEFAULT_CONFIG
    
    def detect_copy_paste(
        self,
        diff: DiffResult,
        metrics: IntervalMetrics
    ) -> Optional[DetectedEvent]:
        """
        Detect a potential copy/paste event.
        
        Criteria (ALL must be true):
        - Δchars_inserted ≥ threshold (default 50)
        - Δt ≤ threshold seconds (default 5)
        - Inserted text has low overlap with prior content
        
        Args:
            diff: The diff result for this interval.
            metrics: The computed metrics for this interval.
        
        Returns:
            DetectedEvent if copy/paste detected, None otherwise.
        """
        # Check character threshold
        if diff.chars_inserted < self.config.paste_chars_threshold:
            return None
        
        # Check time threshold
        if diff.time_delta_seconds > self.config.paste_time_threshold_seconds:
            return None
        
        # Check overlap with prior content
        overlap = DiffEngine.compute_text_overlap(
            diff.inserted_text,
            diff.prior_content
        )
        
        if overlap > self.config.paste_overlap_threshold:
            return None
        
        # All criteria met
        reason = (
            f"Inserted {diff.chars_inserted} chars in "
            f"{diff.time_delta_seconds:.1f}s with {overlap:.1%} overlap"
        )
        
        return DetectedEvent(
            event_type=EventType.COPY_PASTE,
            revision_id=diff.to_revision_id,
            timestamp=diff.to_time,
            wpm=metrics.wpm,
            chars_inserted=diff.chars_inserted,
            time_delta_seconds=diff.time_delta_seconds,
            reason=reason,
        )
    
    def detect_spike(
        self,
        metrics: IntervalMetrics,
        spike_threshold: float
    ) -> Optional[DetectedEvent]:
        """
        Detect a speed spike event.
        
        Criteria:
        - WPM ≥ mean(WPM) + z_score * std(WPM)
        
        Args:
            metrics: The computed metrics for this interval.
            spike_threshold: The WPM threshold for spike detection.
        
        Returns:
            DetectedEvent if spike detected, None otherwise.
        """
        if metrics.wpm < spike_threshold:
            return None
        
        if metrics.is_anomaly:
            # Already flagged as anomaly (e.g., > max_valid_wpm)
            return None
        
        reason = f"WPM of {metrics.wpm:.1f} exceeds threshold {spike_threshold:.1f}"
        
        return DetectedEvent(
            event_type=EventType.SPIKE,
            revision_id=metrics.to_revision_id,
            timestamp=metrics.timestamp,
            wpm=metrics.wpm,
            chars_inserted=metrics.chars_inserted,
            time_delta_seconds=metrics.time_delta_seconds,
            reason=reason,
        )
    
    def detect_idle_burst(
        self,
        prev_diff: DiffResult,
        curr_diff: DiffResult,
        curr_metrics: IntervalMetrics
    ) -> Optional[DetectedEvent]:
        """
        Detect an idle burst event.
        
        Criteria:
        - Previous interval had Δt ≥ threshold minutes (default 10)
        - Current interval has Δchars_inserted ≥ threshold (default 100)
        
        Args:
            prev_diff: The previous diff result.
            curr_diff: The current diff result.
            curr_metrics: The current interval metrics.
        
        Returns:
            DetectedEvent if idle burst detected, None otherwise.
        """
        # Check if previous interval was idle
        idle_threshold_seconds = self.config.idle_time_threshold_minutes * 60
        
        if prev_diff.time_delta_seconds < idle_threshold_seconds:
            return None
        
        # Check if current interval has significant activity
        if curr_diff.chars_inserted < self.config.idle_burst_chars_threshold:
            return None
        
        idle_minutes = prev_diff.time_delta_seconds / 60
        reason = (
            f"Burst of {curr_diff.chars_inserted} chars "
            f"after {idle_minutes:.1f} min idle"
        )
        
        return DetectedEvent(
            event_type=EventType.IDLE_BURST,
            revision_id=curr_diff.to_revision_id,
            timestamp=curr_diff.to_time,
            wpm=curr_metrics.wpm,
            chars_inserted=curr_diff.chars_inserted,
            time_delta_seconds=curr_diff.time_delta_seconds,
            reason=reason,
        )
    
    def detect_all_events(
        self,
        diffs: List[DiffResult],
        metrics: List[IntervalMetrics],
        metrics_engine: MetricsEngine
    ) -> List[DetectedEvent]:
        """
        Detect all events in the revision history.
        
        Args:
            diffs: List of diff results.
            metrics: List of interval metrics (same order as diffs).
            metrics_engine: MetricsEngine instance for threshold calculation.
        
        Returns:
            List of detected events, sorted by timestamp.
        """
        events: List[DetectedEvent] = []
        
        # Calculate spike threshold
        spike_threshold = metrics_engine.get_wpm_threshold_for_spikes(metrics)
        
        # Build a mapping from diff to metrics
        # Note: Some diffs may not have metrics (invalid intervals)
        diff_to_metrics = {}
        metrics_idx = 0
        
        for diff in diffs:
            if metrics_idx < len(metrics):
                m = metrics[metrics_idx]
                if (m.from_revision_id == diff.from_revision_id and 
                    m.to_revision_id == diff.to_revision_id):
                    diff_to_metrics[id(diff)] = m
                    metrics_idx += 1
        
        # Detect events for each interval
        for i, diff in enumerate(diffs):
            m = diff_to_metrics.get(id(diff))
            if m is None:
                continue
            
            # Detect copy/paste
            paste_event = self.detect_copy_paste(diff, m)
            if paste_event:
                events.append(paste_event)
            
            # Detect spike
            spike_event = self.detect_spike(m, spike_threshold)
            if spike_event:
                # Avoid double-counting if already detected as paste
                if not paste_event:
                    events.append(spike_event)
            
            # Detect idle burst
            if i > 0:
                prev_diff = diffs[i - 1]
                idle_event = self.detect_idle_burst(prev_diff, diff, m)
                if idle_event:
                    events.append(idle_event)
        
        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)
        
        return events
    
    def get_event_summary(self, events: List[DetectedEvent]) -> dict:
        """
        Get a summary of detected events.
        
        Args:
            events: List of detected events.
        
        Returns:
            Dictionary with event counts and details.
        """
        summary = {
            "total_events": len(events),
            "copy_paste_count": 0,
            "spike_count": 0,
            "idle_burst_count": 0,
        }
        
        for event in events:
            if event.event_type == EventType.COPY_PASTE:
                summary["copy_paste_count"] += 1
            elif event.event_type == EventType.SPIKE:
                summary["spike_count"] += 1
            elif event.event_type == EventType.IDLE_BURST:
                summary["idle_burst_count"] += 1
        
        return summary
