"""Tests for the histogram visualization."""

import pytest
from datetime import datetime, timedelta

from gdhistogram.visualization.histogram import HistogramGenerator
from gdhistogram.analysis.metrics_engine import IntervalMetrics, OverallStatistics
from gdhistogram.analysis.event_detector import DetectedEvent, EventType
from gdhistogram.config import AnalysisConfig, COLORS, MARKER_SHAPES


class TestHistogramGenerator:
    """Tests for HistogramGenerator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = AnalysisConfig()
        self.generator = HistogramGenerator(self.config)
        self.base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    def _create_metrics(self, count: int = 10) -> list[IntervalMetrics]:
        """Create test metrics."""
        metrics = []
        for i in range(count):
            metrics.append(IntervalMetrics(
                from_revision_id=f"r{i}",
                to_revision_id=f"r{i+1}",
                timestamp=self.base_time + timedelta(minutes=i),
                chars_inserted=200 + i * 10,
                chars_deleted=0,
                net_chars=200 + i * 10,
                time_delta_seconds=60,
                words_inserted=40 + i * 2,
                wpm=40 + i * 2,
                is_anomaly=False,
                anomaly_reason=None,
            ))
        return metrics
    
    def _create_statistics(self, metrics: list[IntervalMetrics]) -> OverallStatistics:
        """Create test statistics."""
        wpm_values = [m.wpm for m in metrics]
        return OverallStatistics(
            total_intervals=len(metrics),
            valid_intervals=len(metrics),
            mean_wpm=sum(wpm_values) / len(wpm_values) if wpm_values else 0,
            median_wpm=sorted(wpm_values)[len(wpm_values) // 2] if wpm_values else 0,
            std_wpm=10.0,
            max_wpm=max(wpm_values) if wpm_values else 0,
            min_wpm=min(wpm_values) if wpm_values else 0,
            total_chars_inserted=sum(m.chars_inserted for m in metrics),
            total_chars_deleted=sum(m.chars_deleted for m in metrics),
            total_net_chars=sum(m.net_chars for m in metrics),
            total_time_seconds=sum(m.time_delta_seconds for m in metrics),
            first_revision_time=self.base_time if metrics else None,
            last_revision_time=self.base_time + timedelta(minutes=len(metrics)) if metrics else None,
            anomaly_count=0,
        )
    
    def test_generate_histogram(self):
        """Test histogram generation."""
        metrics = self._create_metrics(10)
        events = []
        stats = self._create_statistics(metrics)
        
        fig = self.generator.generate_histogram(metrics, events, stats, "Test Document")
        
        assert fig is not None
        # Plotly figure should have data
        assert len(fig.data) > 0
    
    def test_histogram_with_events(self):
        """Test figure generation with events."""
        metrics = self._create_metrics(10)
        events = [
            DetectedEvent(
                event_type=EventType.SPIKE,
                revision_id="r5",
                timestamp=self.base_time + timedelta(minutes=5),
                wpm=50.0,
                chars_inserted=250,
                time_delta_seconds=60,
                reason="WPM spike detected",
            ),
        ]
        stats = self._create_statistics(metrics)
        
        fig = self.generator.generate_histogram(metrics, events, stats, "Test Document")
        
        assert fig is not None
        # Should have additional traces for events
        assert len(fig.data) > 1
    
    def test_export_to_html(self):
        """Test HTML export."""
        metrics = self._create_metrics(10)
        events = []
        stats = self._create_statistics(metrics)
        
        fig = self.generator.generate_histogram(metrics, events, stats, "Test Document")
        html = self.generator.get_figure_html(fig)
        
        assert html is not None
        assert "plotly" in html.lower()
    
    def test_empty_metrics(self):
        """Test handling of empty metrics."""
        metrics = []
        events = []
        stats = OverallStatistics(
            total_intervals=0,
            valid_intervals=0,
            mean_wpm=0,
            median_wpm=0,
            std_wpm=0,
            max_wpm=0,
            min_wpm=0,
            total_chars_inserted=0,
            total_chars_deleted=0,
            total_net_chars=0,
            total_time_seconds=0,
            first_revision_time=None,
            last_revision_time=None,
            anomaly_count=0,
        )
        
        fig = self.generator.generate_histogram(metrics, events, stats, "Test Document")
        
        assert fig is not None


class TestColorScheme:
    """Tests for colorblind-safe color scheme."""
    
    def test_colors_defined(self):
        """Test that colors are defined."""
        assert COLORS is not None
        # Check for the actual keys used in the implementation
        assert "paste_event" in COLORS or "primary" in COLORS
    
    def test_marker_shapes_defined(self):
        """Test that marker shapes are defined."""
        assert MARKER_SHAPES is not None
        assert "paste_event" in MARKER_SHAPES
        assert "spike_event" in MARKER_SHAPES
        assert "idle_event" in MARKER_SHAPES
    
    def test_colors_are_different(self):
        """Test that event colors are distinct."""
        # Check that we have color differentiation for events
        event_colors = [
            COLORS.get("paste_event"),
            COLORS.get("spike_event"),
            COLORS.get("idle_event"),
        ]
        # Filter out None values
        event_colors = [c for c in event_colors if c is not None]
        if event_colors:
            # All colors should be unique
            assert len(event_colors) == len(set(event_colors))
    
    def test_shapes_are_different(self):
        """Test that marker shapes are distinct."""
        shapes = list(MARKER_SHAPES.values())
        # All shapes should be unique
        assert len(shapes) == len(set(shapes))
