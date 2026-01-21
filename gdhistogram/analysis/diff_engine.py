"""Diff engine for comparing revision snapshots."""

from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import List, Optional, Callable
from datetime import datetime

from gdhistogram.api.snapshot_exporter import RevisionSnapshot


@dataclass
class DiffResult:
    """Result of comparing two consecutive revisions."""
    
    # Revision info
    from_revision_id: str
    to_revision_id: str
    from_time: datetime
    to_time: datetime
    
    # Character counts
    chars_inserted: int
    chars_deleted: int
    chars_unchanged: int
    net_chars: int
    
    # Time delta
    time_delta_seconds: float
    
    # Inserted text for overlap analysis
    inserted_text: str
    
    # Context from prior revision (for overlap analysis)
    prior_content: str
    
    @property
    def is_valid(self) -> bool:
        """Check if this diff result is valid for metrics calculation."""
        return self.time_delta_seconds > 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage/export."""
        return {
            "from_revision_id": self.from_revision_id,
            "to_revision_id": self.to_revision_id,
            "from_time": self.from_time.isoformat(),
            "to_time": self.to_time.isoformat(),
            "chars_inserted": self.chars_inserted,
            "chars_deleted": self.chars_deleted,
            "chars_unchanged": self.chars_unchanged,
            "net_chars": self.net_chars,
            "time_delta_seconds": self.time_delta_seconds,
        }


class DiffEngine:
    """
    Engine for computing diffs between revision snapshots.
    
    Uses Python's difflib.SequenceMatcher for deterministic diffing.
    """
    
    def __init__(self):
        """Initialize the diff engine."""
        pass
    
    def compute_diff(
        self,
        from_snapshot: RevisionSnapshot,
        to_snapshot: RevisionSnapshot
    ) -> DiffResult:
        """
        Compute the diff between two consecutive snapshots.
        
        Args:
            from_snapshot: The earlier snapshot.
            to_snapshot: The later snapshot.
        
        Returns:
            DiffResult with the diff statistics.
        """
        from_text = from_snapshot.content
        to_text = to_snapshot.content
        
        # Use SequenceMatcher for deterministic diffing
        matcher = SequenceMatcher(None, from_text, to_text, autojunk=False)
        
        # Calculate character changes
        chars_inserted = 0
        chars_deleted = 0
        chars_unchanged = 0
        inserted_parts: List[str] = []
        
        # Process opcodes: 'replace', 'delete', 'insert', 'equal'
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                chars_unchanged += i2 - i1
            elif tag == "replace":
                chars_deleted += i2 - i1
                chars_inserted += j2 - j1
                inserted_parts.append(to_text[j1:j2])
            elif tag == "delete":
                chars_deleted += i2 - i1
            elif tag == "insert":
                chars_inserted += j2 - j1
                inserted_parts.append(to_text[j1:j2])
        
        # Calculate time delta
        time_delta = (to_snapshot.modified_time - from_snapshot.modified_time).total_seconds()
        
        return DiffResult(
            from_revision_id=from_snapshot.revision_id,
            to_revision_id=to_snapshot.revision_id,
            from_time=from_snapshot.modified_time,
            to_time=to_snapshot.modified_time,
            chars_inserted=chars_inserted,
            chars_deleted=chars_deleted,
            chars_unchanged=chars_unchanged,
            net_chars=chars_inserted - chars_deleted,
            time_delta_seconds=time_delta,
            inserted_text="".join(inserted_parts),
            prior_content=from_text,
        )
    
    def compute_all_diffs(
        self,
        snapshots: List[RevisionSnapshot],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[DiffResult]:
        """
        Compute diffs for all consecutive snapshot pairs.
        
        Args:
            snapshots: List of snapshots sorted by time (ascending).
            progress_callback: Optional callback (completed, total) for progress.
        
        Returns:
            List of DiffResult objects for each consecutive pair.
        """
        if len(snapshots) < 2:
            return []
        
        results: List[DiffResult] = []
        total = len(snapshots) - 1
        
        for i in range(total):
            from_snapshot = snapshots[i]
            to_snapshot = snapshots[i + 1]
            
            diff = self.compute_diff(from_snapshot, to_snapshot)
            results.append(diff)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return results
    
    @staticmethod
    def compute_text_overlap(inserted_text: str, prior_content: str) -> float:
        """
        Compute how much of the inserted text overlaps with prior content.
        
        This is used for copy/paste detection - pasted content often
        comes from elsewhere in the document.
        
        Args:
            inserted_text: The newly inserted text.
            prior_content: The content before the insertion.
        
        Returns:
            Overlap ratio (0.0 to 1.0). Low overlap suggests paste from external source.
        """
        if not inserted_text:
            return 1.0  # No insertion = not a paste
        
        if not prior_content:
            return 0.0  # No prior content to compare
        
        # Use SequenceMatcher to find matching blocks
        matcher = SequenceMatcher(None, inserted_text, prior_content, autojunk=False)
        
        # Calculate ratio of matching content
        matching_chars = sum(
            block.size for block in matcher.get_matching_blocks()
        )
        
        # Return ratio of inserted text that matches prior content
        return matching_chars / len(inserted_text)
