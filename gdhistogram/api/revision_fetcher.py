"""Revision fetcher for Google Drive revisions."""

from typing import List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from googleapiclient.errors import HttpError
from dateutil.parser import isoparse

from gdhistogram.api.google_client import GoogleClient, GoogleClientError


@dataclass
class RevisionMetadata:
    """Metadata for a single revision."""
    id: str
    modified_time: datetime
    last_modifying_user: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "modified_time": self.modified_time.isoformat(),
            "last_modifying_user": self.last_modifying_user,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RevisionMetadata":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            modified_time=isoparse(data["modified_time"]),
            last_modifying_user=data.get("last_modifying_user"),
        )


class RevisionFetcher:
    """
    Fetches revision metadata from Google Drive.
    
    This class handles:
    - Listing all revisions for a document
    - Sorting revisions chronologically
    - Filtering invalid revisions
    - Enforcing revision limits
    """
    
    def __init__(self, google_client: GoogleClient):
        """
        Initialize the revision fetcher.
        
        Args:
            google_client: Initialized GoogleClient instance.
        """
        self.client = google_client
    
    def fetch_revisions(
        self,
        file_id: str,
        max_revisions: int = 2000,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[RevisionMetadata]:
        """
        Fetch all revisions for a document.
        
        Args:
            file_id: The Google Drive file ID.
            max_revisions: Maximum number of revisions to fetch.
            progress_callback: Optional callback (fetched, total) for progress updates.
        
        Returns:
            List of RevisionMetadata objects, sorted by modified_time ascending.
        
        Raises:
            GoogleClientError: If API call fails.
            ValueError: If too many revisions.
        """
        revisions: List[RevisionMetadata] = []
        page_token: Optional[str] = None
        
        try:
            while True:
                # Fetch a page of revisions
                request = self.client.drive_service.revisions().list(
                    fileId=file_id,
                    fields="nextPageToken,revisions(id,modifiedTime,lastModifyingUser)",
                    pageSize=1000,
                    pageToken=page_token
                )
                
                result = request.execute()
                
                # Process revisions
                for rev in result.get("revisions", []):
                    # Skip revisions without required fields
                    if not rev.get("id") or not rev.get("modifiedTime"):
                        continue
                    
                    # Parse user info
                    user = rev.get("lastModifyingUser", {})
                    user_email = user.get("emailAddress") or user.get("displayName")
                    
                    # Parse timestamp
                    try:
                        modified_time = isoparse(rev["modifiedTime"])
                    except Exception:
                        continue
                    
                    revisions.append(RevisionMetadata(
                        id=rev["id"],
                        modified_time=modified_time,
                        last_modifying_user=user_email,
                    ))
                
                # Check revision limit
                if len(revisions) > max_revisions:
                    raise ValueError(
                        f"Document has more than {max_revisions} revisions. "
                        f"Consider increasing the limit or processing in batches."
                    )
                
                # Progress update
                if progress_callback:
                    progress_callback(len(revisions), -1)  # -1 = unknown total
                
                # Check for more pages
                page_token = result.get("nextPageToken")
                if not page_token:
                    break
            
        except HttpError as e:
            if e.resp.status == 403:
                raise GoogleClientError(
                    "Cannot access revision history. The document owner may have "
                    "disabled revision history access."
                )
            elif e.resp.status == 404:
                raise GoogleClientError("Document not found.")
            else:
                raise GoogleClientError(f"API error fetching revisions: {e}")
        
        # Sort by modified time (ascending = oldest first)
        revisions.sort(key=lambda r: r.modified_time)
        
        # Final progress update
        if progress_callback:
            progress_callback(len(revisions), len(revisions))
        
        return revisions
    
    def get_revision_count(self, file_id: str) -> int:
        """
        Get the total number of revisions for a document.
        
        This is a quick check before full fetch.
        
        Args:
            file_id: The Google Drive file ID.
        
        Returns:
            Number of revisions.
        """
        count = 0
        page_token: Optional[str] = None
        
        try:
            while True:
                result = self.client.drive_service.revisions().list(
                    fileId=file_id,
                    fields="nextPageToken,revisions(id)",
                    pageSize=1000,
                    pageToken=page_token
                ).execute()
                
                count += len(result.get("revisions", []))
                
                page_token = result.get("nextPageToken")
                if not page_token:
                    break
            
            return count
            
        except HttpError:
            return 0
