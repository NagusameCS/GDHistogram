"""Tests for the event detector."""

import pytest
from datetime import datetime, timedelta

from gdhistogram.analysis.event_detector import EventDetector, DetectedEvent, EventType
from gdhistogram.analysis.diff_engine import DiffResult
from gdhistogram.analysis.metrics_engine import MetricsEngine, IntervalMetrics
from gdhistogram.config import AnalysisConfig, DEFAULT_CONFIG


class TestEventType:
    """Tests for EventType enum."""
    
    def test_event_types_defined(self):
        """Test that all event types are defined."""
        assert EventType.COPY_PASTE is not None
        assert EventType.SPIKE is not None
        assert EventType.IDLE_BURST is not None
    
    def test_event_type_values(self):
        """Test event type string values."""
        assert EventType.COPY_PASTE.value == "copy_paste"
        assert EventType.SPIKE.value == "spike"
        assert EventType.IDLE_BURST.value == "idle_burst"


class TestDetectedEvent:
    """Tests for DetectedEvent dataclass."""
    
    def test_create_detected_event(self):
        """Test creating a DetectedEvent."""
        event = DetectedEvent(
            event_type=EventType.SPIKE,
            revision_id="r1",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            wpm=150.0,
            chars_inserted=500,
            time_delta_seconds=40.0,
            reason="Test spike event",
        )
        
        assert event.event_type == EventType.SPIKE
        assert event.revision_id == "r1"
        assert event.wpm == 150.0
        assert event.chars_inserted == 500
    
    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = DetectedEvent(
            event_type=EventType.COPY_PASTE,
            revision_id="r2",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            wpm=300.0,
            chars_inserted=1000,
            time_delta_seconds=10.0,
            reason="Paste detected",
        )
        
        data = event.to_dict()
        
        assert data["event_type"] == "copy_paste"
        assert data["revision_id"] == "r2"
        assert data["wpm"] == 300.0
        assert data["chars_inserted"] == 1000


class TestEventDetector:
    """Tests for EventDetector class."""
    
    def test_detector_initialization(self):
        """Test that detector can be initialized."""
        detector = EventDetector()
        assert detector is not None
        assert detector.config is not None
    
    def test_detector_with_config(self):
        """Test detector with custom config."""
        config = AnalysisConfig(spike_z_score_threshold=2.0)
        detector = EventDetector(config)
        
        assert detector.config.spike_z_score_threshold == 2.0
    
    def test_detect_copy_paste_under_threshold(self):
        """Test that small inserts don't trigger copy/paste detection."""
        detector = EventDetector()
        
        # Create a diff with few characters
        diff = DiffResult(
            from_revision_id="r1",
            to_revision_id="r2",
            from_time=datetime(2024, 1, 1, 12, 0, 0),
            to_time=datetime(2024, 1, 1, 12, 0, 2),
            chars_inserted=20,  # Below threshold (50)
            chars_deleted=0,
            chars_unchanged=100,
            net_chars=20,
            time_delta_seconds=2.0,
            inserted_text="This is a small insert",
            prior_content="Some prior content",
        )
        
        # Create corresponding metrics
        metrics = IntervalMetrics(
            from_revision_id="r1",
            to_revision_id="r2",
            timestamp=datetime(2024, 1, 1, 12, 0, 2),
            chars_inserted=20,
            chars_deleted=0,
            net_chars=20,
            time_delta_seconds=2.0,
            words_inserted=4,
            wpm=120.0,
        )
        
        event = detector.detect_copy_paste(diff, metrics)
        
        # Should not detect as copy/paste (below char threshold)
        assert event is None
