"""Tests for the diff engine."""

import pytest
from datetime import datetime, timedelta

from gdhistogram.analysis.diff_engine import DiffEngine, DiffResult
from gdhistogram.api.snapshot_exporter import RevisionSnapshot


class TestDiffEngine:
    """Tests for DiffEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DiffEngine()
    
    def _create_snapshot(
        self,
        revision_id: str,
        content: str,
        offset_minutes: int = 0
    ) -> RevisionSnapshot:
        """Create a test snapshot."""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        return RevisionSnapshot(
            revision_id=revision_id,
            modified_time=base_time + timedelta(minutes=offset_minutes),
            content=content,
            char_count=len(content),
        )
    
    def test_no_changes(self):
        """Test diff with identical content."""
        snapshot1 = self._create_snapshot("r1", "Hello world", 0)
        snapshot2 = self._create_snapshot("r2", "Hello world", 5)
        
        result = self.engine.compute_diff(snapshot1, snapshot2)
        
        assert result.chars_inserted == 0
        assert result.chars_deleted == 0
        assert result.chars_unchanged == 11
        assert result.net_chars == 0
    
    def test_pure_insertion(self):
        """Test diff with only insertions."""
        snapshot1 = self._create_snapshot("r1", "Hello", 0)
        snapshot2 = self._create_snapshot("r2", "Hello world", 5)
        
        result = self.engine.compute_diff(snapshot1, snapshot2)
        
        assert result.chars_inserted == 6  # " world"
        assert result.chars_deleted == 0
        assert result.net_chars == 6
    
    def test_pure_deletion(self):
        """Test diff with only deletions."""
        snapshot1 = self._create_snapshot("r1", "Hello world", 0)
        snapshot2 = self._create_snapshot("r2", "Hello", 5)
        
        result = self.engine.compute_diff(snapshot1, snapshot2)
        
        assert result.chars_inserted == 0
        assert result.chars_deleted == 6  # " world"
        assert result.net_chars == -6
    
    def test_replacement(self):
        """Test diff with replacement."""
        snapshot1 = self._create_snapshot("r1", "Hello world", 0)
        snapshot2 = self._create_snapshot("r2", "Hello there", 5)
        
        result = self.engine.compute_diff(snapshot1, snapshot2)
        
        # "world" -> "there" - difflib may find partial matches
        # The exact counts depend on the SequenceMatcher algorithm
        # Just verify that we have both insertions and deletions
        assert result.chars_inserted > 0
        assert result.chars_deleted > 0
        # Net change should be 0 (same length strings)
        assert result.net_chars == 0
    
    def test_time_delta(self):
        """Test time delta calculation."""
        snapshot1 = self._create_snapshot("r1", "Hello", 0)
        snapshot2 = self._create_snapshot("r2", "Hello world", 10)
        
        result = self.engine.compute_diff(snapshot1, snapshot2)
        
        assert result.time_delta_seconds == 600  # 10 minutes
    
    def test_inserted_text_captured(self):
        """Test that inserted text is captured."""
        snapshot1 = self._create_snapshot("r1", "Hello", 0)
        snapshot2 = self._create_snapshot("r2", "Hello world", 5)
        
        result = self.engine.compute_diff(snapshot1, snapshot2)
        
        assert " world" in result.inserted_text
    
    def test_compute_all_diffs(self):
        """Test computing diffs for multiple snapshots."""
        snapshots = [
            self._create_snapshot("r1", "A", 0),
            self._create_snapshot("r2", "AB", 5),
            self._create_snapshot("r3", "ABC", 10),
        ]
        
        results = self.engine.compute_all_diffs(snapshots)
        
        assert len(results) == 2
        assert results[0].chars_inserted == 1  # "B"
        assert results[1].chars_inserted == 1  # "C"
    
    def test_empty_snapshots(self):
        """Test with empty snapshot list."""
        results = self.engine.compute_all_diffs([])
        assert results == []
    
    def test_single_snapshot(self):
        """Test with single snapshot."""
        snapshots = [self._create_snapshot("r1", "Hello", 0)]
        results = self.engine.compute_all_diffs(snapshots)
        assert results == []


class TestTextOverlap:
    """Tests for text overlap calculation."""
    
    def test_full_overlap(self):
        """Test text that fully overlaps."""
        inserted = "Hello"
        prior = "Hello world"
        
        overlap = DiffEngine.compute_text_overlap(inserted, prior)
        
        assert overlap >= 0.9  # High overlap
    
    def test_no_overlap(self):
        """Test text with no overlap."""
        inserted = "XYZ123"
        prior = "Hello world"
        
        overlap = DiffEngine.compute_text_overlap(inserted, prior)
        
        assert overlap < 0.3  # Low overlap
    
    def test_empty_inserted(self):
        """Test with empty inserted text."""
        overlap = DiffEngine.compute_text_overlap("", "Hello")
        assert overlap == 1.0
    
    def test_empty_prior(self):
        """Test with empty prior content."""
        overlap = DiffEngine.compute_text_overlap("Hello", "")
        assert overlap == 0.0
