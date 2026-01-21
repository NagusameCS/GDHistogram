"""SQLite database for caching revision data."""

import sqlite3
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from contextlib import contextmanager

from gdhistogram.config import DATABASE_FILE, APP_DATA_DIR
from gdhistogram.api.revision_fetcher import RevisionMetadata
from gdhistogram.api.snapshot_exporter import RevisionSnapshot


class Database:
    """
    SQLite database for local caching of revision data.
    
    This is a read-only analysis cache - never writes to Google.
    """
    
    SCHEMA_VERSION = 1
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the database.
        
        Args:
            db_path: Path to database file. Uses default if not provided.
        """
        self.db_path = db_path or DATABASE_FILE
        self._ensure_directory()
        self._init_schema()
    
    def _ensure_directory(self) -> None:
        """Ensure the database directory exists."""
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def _connection(self):
        """Get a database connection context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_schema(self) -> None:
        """Initialize the database schema."""
        with self._connection() as conn:
            cursor = conn.cursor()
            
            # Schema version table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
            """)
            
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    file_id TEXT PRIMARY KEY,
                    title TEXT,
                    owner TEXT,
                    created_time TEXT,
                    modified_time TEXT,
                    last_analyzed TEXT
                )
            """)
            
            # Revisions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    revision_id TEXT NOT NULL,
                    modified_time TEXT NOT NULL,
                    last_modifying_user TEXT,
                    UNIQUE(file_id, revision_id)
                )
            """)
            
            # Snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    revision_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    char_count INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    UNIQUE(file_id, revision_id)
                )
            """)
            
            # Analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    analysis_time TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    results_json TEXT NOT NULL,
                    revision_hash TEXT NOT NULL
                )
            """)
            
            # Create indices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_revisions_file_id 
                ON revisions(file_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_file_id 
                ON snapshots(file_id)
            """)
            
            # Set schema version
            cursor.execute("INSERT OR REPLACE INTO schema_version VALUES (?)",
                          (self.SCHEMA_VERSION,))
    
    def save_document_info(
        self,
        file_id: str,
        title: str,
        owner: str,
        created_time: str,
        modified_time: str
    ) -> None:
        """Save document metadata."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO documents 
                (file_id, title, owner, created_time, modified_time, last_analyzed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (file_id, title, owner, created_time, modified_time,
                  datetime.now(timezone.utc).isoformat()))
    
    def save_revisions(
        self,
        file_id: str,
        revisions: List[RevisionMetadata]
    ) -> None:
        """Save revision metadata."""
        with self._connection() as conn:
            cursor = conn.cursor()
            
            for rev in revisions:
                cursor.execute("""
                    INSERT OR REPLACE INTO revisions 
                    (file_id, revision_id, modified_time, last_modifying_user)
                    VALUES (?, ?, ?, ?)
                """, (file_id, rev.id, rev.modified_time.isoformat(),
                      rev.last_modifying_user))
    
    def get_cached_revisions(self, file_id: str) -> List[RevisionMetadata]:
        """Get cached revision metadata."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT revision_id, modified_time, last_modifying_user
                FROM revisions
                WHERE file_id = ?
                ORDER BY modified_time ASC
            """, (file_id,))
            
            return [
                RevisionMetadata.from_dict({
                    "id": row["revision_id"],
                    "modified_time": row["modified_time"],
                    "last_modifying_user": row["last_modifying_user"],
                })
                for row in cursor.fetchall()
            ]
    
    def save_snapshot(
        self,
        file_id: str,
        snapshot: RevisionSnapshot
    ) -> None:
        """Save a revision snapshot."""
        content_hash = hashlib.sha256(snapshot.content.encode()).hexdigest()
        
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO snapshots 
                (file_id, revision_id, content, char_count, content_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (file_id, snapshot.revision_id, snapshot.content,
                  snapshot.char_count, content_hash))
    
    def get_cached_snapshot(
        self,
        file_id: str,
        revision_id: str
    ) -> Optional[RevisionSnapshot]:
        """Get a cached snapshot if available."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.revision_id, r.modified_time, s.content, s.char_count
                FROM snapshots s
                JOIN revisions r ON s.file_id = r.file_id 
                    AND s.revision_id = r.revision_id
                WHERE s.file_id = ? AND s.revision_id = ?
            """, (file_id, revision_id))
            
            row = cursor.fetchone()
            if row:
                return RevisionSnapshot.from_dict({
                    "revision_id": row["revision_id"],
                    "modified_time": row["modified_time"],
                    "content": row["content"],
                    "char_count": row["char_count"],
                })
            return None
    
    def get_all_cached_snapshots(
        self,
        file_id: str
    ) -> Dict[str, RevisionSnapshot]:
        """Get all cached snapshots for a document."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.revision_id, r.modified_time, s.content, s.char_count
                FROM snapshots s
                JOIN revisions r ON s.file_id = r.file_id 
                    AND s.revision_id = r.revision_id
                WHERE s.file_id = ?
            """, (file_id,))
            
            result = {}
            for row in cursor.fetchall():
                snapshot = RevisionSnapshot.from_dict({
                    "revision_id": row["revision_id"],
                    "modified_time": row["modified_time"],
                    "content": row["content"],
                    "char_count": row["char_count"],
                })
                result[snapshot.revision_id] = snapshot
            
            return result
    
    def save_analysis_results(
        self,
        file_id: str,
        config: dict,
        results: dict,
        revision_ids: List[str]
    ) -> None:
        """Save analysis results."""
        # Create hash of revision IDs for integrity check
        revision_hash = hashlib.sha256(
            "|".join(sorted(revision_ids)).encode()
        ).hexdigest()
        
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analysis_results 
                (file_id, analysis_time, config_json, results_json, revision_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (file_id, datetime.now(timezone.utc).isoformat(),
                  json.dumps(config), json.dumps(results), revision_hash))
    
    def get_revision_hash(self, file_id: str) -> Optional[str]:
        """Get the hash of revision IDs for integrity checking."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT revision_id FROM revisions
                WHERE file_id = ?
                ORDER BY revision_id
            """, (file_id,))
            
            revision_ids = [row["revision_id"] for row in cursor.fetchall()]
            if not revision_ids:
                return None
            
            return hashlib.sha256(
                "|".join(sorted(revision_ids)).encode()
            ).hexdigest()
    
    def clear_document_cache(self, file_id: str) -> None:
        """Clear all cached data for a document."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM snapshots WHERE file_id = ?", (file_id,))
            cursor.execute("DELETE FROM revisions WHERE file_id = ?", (file_id,))
            cursor.execute("DELETE FROM documents WHERE file_id = ?", (file_id,))
            cursor.execute("DELETE FROM analysis_results WHERE file_id = ?", (file_id,))
    
    def clear_all(self) -> None:
        """Clear all cached data."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM snapshots")
            cursor.execute("DELETE FROM revisions")
            cursor.execute("DELETE FROM documents")
            cursor.execute("DELETE FROM analysis_results")


class CacheManager:
    """
    Manager for caching revision data to avoid re-fetching.
    
    Implements the caching strategy:
    - Cache exported revisions locally
    - Never re-fetch unchanged revisions
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Initialize the cache manager.
        
        Args:
            database: Database instance. Creates default if not provided.
        """
        self.db = database or Database()
    
    def get_missing_revision_ids(
        self,
        file_id: str,
        revisions: List[RevisionMetadata]
    ) -> List[str]:
        """
        Get revision IDs that are not cached.
        
        Args:
            file_id: Document file ID.
            revisions: List of revision metadata.
        
        Returns:
            List of revision IDs that need to be fetched.
        """
        cached_snapshots = self.db.get_all_cached_snapshots(file_id)
        return [
            rev.id for rev in revisions
            if rev.id not in cached_snapshots
        ]
    
    def get_or_fetch_snapshots(
        self,
        file_id: str,
        revisions: List[RevisionMetadata],
        fetch_func
    ) -> List[RevisionSnapshot]:
        """
        Get snapshots, fetching only missing ones.
        
        Args:
            file_id: Document file ID.
            revisions: List of revision metadata.
            fetch_func: Function to fetch a single snapshot (revision) -> snapshot.
        
        Returns:
            List of snapshots in revision order.
        """
        cached = self.db.get_all_cached_snapshots(file_id)
        snapshots = []
        
        for rev in revisions:
            if rev.id in cached:
                snapshots.append(cached[rev.id])
            else:
                snapshot = fetch_func(rev)
                self.db.save_snapshot(file_id, snapshot)
                snapshots.append(snapshot)
        
        return snapshots
