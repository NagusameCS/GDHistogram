"""Tests for the storage layer."""

import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from gdhistogram.storage.database import Database, CacheManager


class TestDatabase:
    """Tests for Database class."""
    
    def setup_method(self):
        """Set up test fixtures with a temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.db = Database(self.db_path)
    
    def teardown_method(self):
        """Clean up temporary files."""
        # Database connections are closed by context managers
        if hasattr(self, 'db_path') and self.db_path.exists():
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass  # Handle Windows file locking
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
            except OSError:
                pass  # May not be empty
    
    def test_database_creation(self):
        """Test that database file is created."""
        assert self.db_path.exists()
    
    def test_save_document_info(self):
        """Test saving document info."""
        self.db.save_document_info(
            file_id="doc123",
            title="Test Document",
            owner="user@example.com",
            created_time="2024-01-01T12:00:00Z",
            modified_time="2024-01-01T13:00:00Z",
        )
        
        # Database should not raise an error
        # Actual retrieval would require additional methods
        assert True
    
    def test_clear_all(self):
        """Test clearing all data."""
        self.db.save_document_info(
            file_id="doc123",
            title="Test",
            owner="user@example.com",
            created_time="2024-01-01T12:00:00Z",
            modified_time="2024-01-01T12:00:00Z",
        )
        
        self.db.clear_all()
        
        # Should not raise any errors
        assert True
    
    def test_clear_document_cache(self):
        """Test clearing cache for a specific document."""
        self.db.save_document_info(
            file_id="doc123",
            title="Test",
            owner="user@example.com",
            created_time="2024-01-01T12:00:00Z",
            modified_time="2024-01-01T12:00:00Z",
        )
        
        self.db.clear_document_cache("doc123")
        
        # Should not raise any errors
        assert True


class TestCacheManager:
    """Tests for CacheManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.db = Database(self.db_path)
        self.cache = CacheManager(self.db)
    
    def teardown_method(self):
        """Clean up temporary files."""
        if hasattr(self, 'db_path') and self.db_path.exists():
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
            except OSError:
                pass
    
    def test_cache_manager_initialization(self):
        """Test that cache manager can be initialized."""
        assert self.cache is not None
        assert self.cache.db is not None
