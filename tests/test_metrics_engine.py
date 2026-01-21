"""Tests for the metrics engine."""

import pytest
from datetime import datetime, timedelta

from gdhistogram.analysis.metrics_engine import MetricsEngine, IntervalMetrics
from gdhistogram.analysis.diff_engine import DiffResult
from gdhistogram.config import AnalysisConfig


class TestMetricsEngine:
    """Tests for MetricsEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = AnalysisConfig(
            chars_per_word=5,
            max_valid_wpm=500,
            spike_z_score_threshold=3.0,
        )
        self.engine = MetricsEngine(self.config)
    
    def _create_diff(
        self,
        chars_inserted: int,
        chars_deleted: int,
        time_delta_seconds: float
    ) -> DiffResult:
        """Create a test diff result."""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        return DiffResult(
            from_revision_id="r1",
            to_revision_id="r2",
            from_time=base_time,
            to_time=base_time + timedelta(seconds=time_delta_seconds),
            chars_inserted=chars_inserted,
            chars_deleted=chars_deleted,
            chars_unchanged=100,
            net_chars=chars_inserted - chars_deleted,
            time_delta_seconds=time_delta_seconds,
            inserted_text="x" * chars_inserted,
            prior_content="y" * 100,
        )
    
    def test_wpm_calculation(self):
        """Test basic WPM calculation."""
        # 100 chars in 60 seconds = 20 words/min
        diff = self._create_diff(100, 0, 60)
        
        metrics = self.engine.compute_interval_metrics(diff)
        
        assert metrics is not None
        assert metrics.words_inserted == 20  # 100 / 5
        assert metrics.wpm == 20
    
    def test_wpm_with_deletion(self):
        """Test WPM with deletions."""
        # WPM is based on insertions only
        diff = self._create_diff(100, 50, 60)
        
        metrics = self.engine.compute_interval_metrics(diff)
        
        assert metrics is not None
        assert metrics.wpm == 20  # Based on 100 inserted chars
        assert metrics.net_chars == 50
    
    def test_zero_time_delta(self):
        """Test with zero time delta."""
        diff = self._create_diff(100, 0, 0)
        
        metrics = self.engine.compute_interval_metrics(diff)
        
        assert metrics is None  # Invalid interval
    
    def test_high_wpm_flagged(self):
        """Test that extremely high WPM is flagged as anomaly."""
        # 1000 chars in 6 seconds = 200 words / 0.1 min = 2000 WPM
        diff = self._create_diff(1000, 0, 6)
        
        metrics = self.engine.compute_interval_metrics(diff)
        
        assert metrics is not None
        assert metrics.is_anomaly is True
        assert "exceeds maximum" in metrics.anomaly_reason.lower()
    
    def test_compute_all_metrics(self):
        """Test computing metrics for multiple diffs."""
        diffs = [
            self._create_diff(50, 0, 60),
            self._create_diff(100, 0, 60),
            self._create_diff(75, 25, 60),
        ]
        
        metrics = self.engine.compute_all_metrics(diffs)
        
        assert len(metrics) == 3
        assert metrics[0].wpm == 10
        assert metrics[1].wpm == 20
        assert metrics[2].wpm == 15
    
    def test_statistics_calculation(self):
        """Test overall statistics calculation."""
        diffs = [
            self._create_diff(50, 0, 60),   # 10 WPM
            self._create_diff(100, 0, 60),  # 20 WPM
            self._create_diff(150, 0, 60),  # 30 WPM
        ]
        
        metrics = self.engine.compute_all_metrics(diffs)
        stats = self.engine.compute_statistics(metrics, diffs)
        
        assert stats.valid_intervals == 3
        assert stats.mean_wpm == 20  # (10+20+30)/3
        assert stats.median_wpm == 20
        assert stats.max_wpm == 30
        assert stats.min_wpm == 10
        assert stats.total_chars_inserted == 300
    
    def test_spike_threshold(self):
        """Test spike threshold calculation."""
        diffs = [
            self._create_diff(50, 0, 60),   # 10 WPM
            self._create_diff(100, 0, 60),  # 20 WPM
            self._create_diff(150, 0, 60),  # 30 WPM
        ]
        
        metrics = self.engine.compute_all_metrics(diffs)
        threshold = self.engine.get_wpm_threshold_for_spikes(metrics)
        
        # threshold = mean + 3 * std
        # mean = 20, std = 10
        # threshold = 20 + 30 = 50
        assert threshold == pytest.approx(50, abs=1)
