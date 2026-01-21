"""Snapshot exporter for revision content."""

import io
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from gdhistogram.api.google_client import GoogleClient, GoogleClientError
from gdhistogram.api.revision_fetcher import RevisionMetadata


@dataclass
class RevisionSnapshot:
    """A snapshot of document content at a specific revision."""
    revision_id: str
    modified_time: datetime
    content: str
    char_count: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "revision_id": self.revision_id,
            "modified_time": self.modified_time.isoformat(),
            "content": self.content,
            "char_count": self.char_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RevisionSnapshot":
        """Create from dictionary."""
        from dateutil.parser import isoparse
        return cls(
            revision_id=data["revision_id"],
            modified_time=isoparse(data["modified_time"]),
            content=data["content"],
            char_count=data["char_count"],
        )


class SnapshotExporter:
    """
    Exports document content at specific revisions.
    
    This class handles:
    - Exporting revision content as plain text
    - Normalizing text (line endings, whitespace)
    - Caching exported content
    """
    
    def __init__(self, google_client: GoogleClient):
        """
        Initialize the snapshot exporter.
        
        Args:
            google_client: Initialized GoogleClient instance.
        """
        self.client = google_client
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize document text for consistent comparison.
        
        Args:
            text: Raw document text.
        
        Returns:
            Normalized text.
        """
        # Normalize line endings to \n
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Strip trailing whitespace from each line
        lines = [line.rstrip() for line in text.split("\n")]
        
        # Rejoin
        text = "\n".join(lines)
        
        # Strip leading/trailing whitespace from entire document
        text = text.strip()
        
        return text
    
    def export_revision(
        self,
        file_id: str,
        revision: RevisionMetadata
    ) -> RevisionSnapshot:
        """
        Export a single revision's content.
        
        Args:
            file_id: The Google Drive file ID.
            revision: The revision metadata.
        
        Returns:
            RevisionSnapshot with the content.
        
        Raises:
            GoogleClientError: If export fails.
        """
        try:
            # Export as plain text
            # Note: For Google Docs, we need to use export with revision
            request = self.client.drive_service.revisions().get_media(
                fileId=file_id,
                revisionId=revision.id,
            )
            
            # Download content
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            # Decode content
            content = buffer.getvalue().decode("utf-8", errors="replace")
            
            # Normalize
            content = self.normalize_text(content)
            
            return RevisionSnapshot(
                revision_id=revision.id,
                modified_time=revision.modified_time,
                content=content,
                char_count=len(content),
            )
            
        except HttpError as e:
            if e.resp.status == 403:
                raise GoogleClientError(
                    f"Cannot export revision {revision.id}. Access denied."
                )
            elif e.resp.status == 404:
                raise GoogleClientError(
                    f"Revision {revision.id} not found or cannot be exported."
                )
            else:
                raise GoogleClientError(f"Error exporting revision: {e}")
        except Exception as e:
            raise GoogleClientError(f"Unexpected error exporting revision: {e}")
    
    def export_all_revisions(
        self,
        file_id: str,
        revisions: list[RevisionMetadata],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> list[RevisionSnapshot]:
        """
        Export all revisions' content.
        
        Args:
            file_id: The Google Drive file ID.
            revisions: List of revision metadata.
            progress_callback: Optional callback (completed, total) for progress.
            cancel_check: Optional function that returns True if cancelled.
        
        Returns:
            List of RevisionSnapshot objects.
        
        Raises:
            GoogleClientError: If any export fails.
        """
        snapshots: list[RevisionSnapshot] = []
        total = len(revisions)
        
        for i, revision in enumerate(revisions):
            # Check for cancellation
            if cancel_check and cancel_check():
                raise GoogleClientError("Export cancelled by user.")
            
            # Export this revision
            snapshot = self.export_revision(file_id, revision)
            snapshots.append(snapshot)
            
            # Progress update
            if progress_callback:
                progress_callback(i + 1, total)
        
        return snapshots
