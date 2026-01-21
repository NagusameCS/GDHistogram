"""Google API client wrapper."""

import re
from typing import Optional, Tuple
from dataclasses import dataclass

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from gdhistogram.config import GOOGLE_DOC_MIME_TYPE


@dataclass
class DocumentInfo:
    """Information about a Google Doc."""
    file_id: str
    title: str
    mime_type: str
    owner: str
    created_time: str
    modified_time: str
    
    @property
    def is_google_doc(self) -> bool:
        """Check if this is a Google Doc."""
        return self.mime_type == GOOGLE_DOC_MIME_TYPE


class GoogleClientError(Exception):
    """Error interacting with Google APIs."""
    pass


class DocumentNotFoundError(GoogleClientError):
    """Document not found or not accessible."""
    pass


class NotAGoogleDocError(GoogleClientError):
    """The file is not a Google Doc."""
    pass


class GoogleClient:
    """
    Client for interacting with Google Drive and Docs APIs.
    
    This class provides a unified interface for:
    - Validating document access
    - Fetching document metadata
    - Managing API service instances
    """
    
    # Regex patterns for extracting file ID from URLs
    URL_PATTERNS = [
        # https://docs.google.com/document/d/{fileId}/edit
        r"docs\.google\.com/document/d/([a-zA-Z0-9_-]+)",
        # https://drive.google.com/file/d/{fileId}/view
        r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
        # https://drive.google.com/open?id={fileId}
        r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
    ]
    
    def __init__(self, credentials: Credentials):
        """
        Initialize the Google client.
        
        Args:
            credentials: Valid OAuth credentials.
        """
        self._credentials = credentials
        self._drive_service = None
        self._docs_service = None
    
    @property
    def drive_service(self):
        """Get the Drive API service (lazy initialization)."""
        if self._drive_service is None:
            self._drive_service = build("drive", "v3", credentials=self._credentials)
        return self._drive_service
    
    @property
    def docs_service(self):
        """Get the Docs API service (lazy initialization)."""
        if self._docs_service is None:
            self._docs_service = build("docs", "v1", credentials=self._credentials)
        return self._docs_service
    
    @classmethod
    def extract_file_id(cls, input_str: str) -> str:
        """
        Extract file ID from a URL or return input if already an ID.
        
        Args:
            input_str: Google Docs URL or file ID.
        
        Returns:
            The extracted file ID.
        
        Raises:
            ValueError: If no valid file ID could be extracted.
        """
        input_str = input_str.strip()
        
        # Try URL patterns
        for pattern in cls.URL_PATTERNS:
            match = re.search(pattern, input_str)
            if match:
                return match.group(1)
        
        # Check if it's already a valid file ID format
        # File IDs are alphanumeric with underscores and hyphens
        if re.match(r"^[a-zA-Z0-9_-]+$", input_str) and len(input_str) > 10:
            return input_str
        
        raise ValueError(
            "Invalid input. Please provide a valid Google Docs URL or file ID."
        )
    
    def get_document_info(self, file_id: str) -> DocumentInfo:
        """
        Get information about a document.
        
        Args:
            file_id: The Google Drive file ID.
        
        Returns:
            DocumentInfo object with document metadata.
        
        Raises:
            DocumentNotFoundError: If the document doesn't exist or isn't accessible.
            NotAGoogleDocError: If the file is not a Google Doc.
            GoogleClientError: For other API errors.
        """
        try:
            result = self.drive_service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,owners,createdTime,modifiedTime"
            ).execute()
            
            # Get owner email
            owners = result.get("owners", [])
            owner = owners[0].get("emailAddress", "Unknown") if owners else "Unknown"
            
            doc_info = DocumentInfo(
                file_id=result["id"],
                title=result.get("name", "Untitled"),
                mime_type=result.get("mimeType", ""),
                owner=owner,
                created_time=result.get("createdTime", ""),
                modified_time=result.get("modifiedTime", ""),
            )
            
            # Verify it's a Google Doc
            if not doc_info.is_google_doc:
                raise NotAGoogleDocError(
                    f"The file '{doc_info.title}' is not a Google Doc. "
                    f"MIME type: {doc_info.mime_type}"
                )
            
            return doc_info
            
        except HttpError as e:
            if e.resp.status == 404:
                raise DocumentNotFoundError(
                    f"Document not found. The file may not exist or you may not have access."
                )
            elif e.resp.status == 403:
                raise DocumentNotFoundError(
                    f"Access denied. You don't have permission to view this document."
                )
            else:
                raise GoogleClientError(f"API error: {e}")
        except NotAGoogleDocError:
            raise
        except Exception as e:
            raise GoogleClientError(f"Unexpected error: {e}")
    
    def validate_document(self, input_str: str) -> Tuple[bool, str, Optional[DocumentInfo]]:
        """
        Validate a document URL or ID.
        
        Args:
            input_str: Google Docs URL or file ID.
        
        Returns:
            Tuple of (is_valid, message, document_info)
        """
        try:
            file_id = self.extract_file_id(input_str)
        except ValueError as e:
            return False, str(e), None
        
        try:
            doc_info = self.get_document_info(file_id)
            return True, f"Document found: {doc_info.title}", doc_info
        except DocumentNotFoundError as e:
            return False, str(e), None
        except NotAGoogleDocError as e:
            return False, str(e), None
        except GoogleClientError as e:
            return False, str(e), None
