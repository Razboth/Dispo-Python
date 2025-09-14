"""
Enhanced database management with connection pooling and proper indexing
"""
import os
import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
import threading
import time

from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, OperationFailure
from gridfs import GridFS
from bson.objectid import ObjectId
import pymongo.errors

from ..utils.exceptions import DatabaseError, BackupError
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Enhanced database manager with connection pooling and monitoring"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config: ConfigManager = None):
        """Singleton pattern for database connection"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: ConfigManager = None):
        """Initialize database connection with pooling"""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.config = config or ConfigManager()
        self.db_config = self.config.get_database_config()

        # Connection pooling settings
        connection_params = {
            'host': self.db_config['host'],
            'port': self.db_config['port'],
            'maxPoolSize': 50,
            'minPoolSize': 10,
            'maxIdleTimeMS': 300000,  # 5 minutes
            'waitQueueTimeoutMS': 5000,
            'serverSelectionTimeoutMS': 5000,
            'connectTimeoutMS': 10000,
            'socketTimeoutMS': 20000,
            'retryWrites': True,
            'retryReads': True
        }

        # Add authentication if configured
        if self.db_config.get('username') and self.db_config.get('password'):
            connection_params['username'] = self.db_config['username']
            connection_params['password'] = self.db_config['password']
            connection_params['authSource'] = self.db_config.get('auth_source', 'admin')

        # Add SSL if configured
        if self.db_config.get('use_ssl'):
            connection_params['tls'] = True
            connection_params['tlsAllowInvalidCertificates'] = False

        try:
            self.client = MongoClient(**connection_params)
            self.db = self.client[self.db_config['database']]

            # Test connection
            self.client.admin.command('ping')

            # Initialize collections
            self.documents = self.db['documents']
            self.users = self.db['users']
            self.templates = self.db['templates']
            self.audit_log = self.db['audit_log']
            self.counters = self.db['counters']
            self.notifications = self.db['notifications']
            self.workflow = self.db['workflow']

            # Initialize GridFS for file storage
            self.fs = GridFS(self.db)

            # Create indexes
            self._create_indexes()

            logger.info(f"Database connected: {self.db_config['host']}:{self.db_config['port']}")

        except ConnectionFailure as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DatabaseError(f"Database connection failed: {e}")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    def _create_indexes(self):
        """Create optimized indexes for all collections"""
        try:
            # Document collection indexes
            document_indexes = [
                ('nomor_surat', ASCENDING),
                ('tanggal_surat', DESCENDING),
                ('jenis_dokumen', ASCENDING),
                ('status', ASCENDING),
                ('created_at', DESCENDING),
                ('updated_at', DESCENDING),
                ([('nomor_surat', TEXT), ('perihal', TEXT), ('asal_surat', TEXT)], 'text_search'),
                ([('jenis_dokumen', ASCENDING), ('status', ASCENDING), ('tanggal_surat', DESCENDING)], 'compound_filter'),
            ]

            for index in document_indexes:
                if isinstance(index, tuple) and len(index) == 2:
                    if isinstance(index[0], list):
                        # Compound index
                        self.documents.create_index(index[0], name=index[1])
                    else:
                        # Single field index
                        self.documents.create_index([(index[0], index[1])])

            # User collection indexes (handled in User model)

            # Audit log indexes
            self.audit_log.create_index([('timestamp', DESCENDING)])
            self.audit_log.create_index([('user_id', ASCENDING)])
            self.audit_log.create_index([('action', ASCENDING)])
            self.audit_log.create_index([('document_id', ASCENDING)])

            # Notification indexes
            self.notifications.create_index([('user_id', ASCENDING)])
            self.notifications.create_index([('read', ASCENDING)])
            self.notifications.create_index([('created_at', DESCENDING)])

            # Workflow indexes
            self.workflow.create_index([('document_id', ASCENDING)])
            self.workflow.create_index([('status', ASCENDING)])
            self.workflow.create_index([('assigned_to', ASCENDING)])

            logger.info("Database indexes created successfully")

        except OperationFailure as e:
            logger.error(f"Failed to create indexes: {e}")

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        with self.client.start_session() as session:
            with session.start_transaction():
                try:
                    yield session
                except Exception as e:
                    logger.error(f"Transaction failed: {e}")
                    raise

    def get_next_sequence(self, sequence_name: str) -> int:
        """Get next sequence number for auto-increment fields"""
        result = self.counters.find_one_and_update(
            {'_id': sequence_name},
            {'$inc': {'sequence_value': 1}},
            upsert=True,
            return_document=True
        )
        return result['sequence_value']

    def insert_document(self, data: Dict[str, Any], user_id: str = None) -> str:
        """Insert document with audit logging"""
        try:
            # Add metadata
            data['_id'] = ObjectId()
            data['document_number'] = self.get_next_sequence('document_number')
            data['created_at'] = datetime.utcnow()
            data['updated_at'] = datetime.utcnow()
            data['created_by'] = user_id
            data['updated_by'] = user_id
            data['version'] = 1
            data['status'] = data.get('status', 'draft')

            # Insert document
            result = self.documents.insert_one(data)

            # Log audit
            self._log_audit('document_created', user_id, str(result.inserted_id), data)

            logger.info(f"Document inserted: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to insert document: {e}")
            raise DatabaseError(f"Failed to insert document: {e}")

    def update_document(self, document_id: str, data: Dict[str, Any], user_id: str = None) -> bool:
        """Update document with version control"""
        try:
            # Get current document for version control
            current = self.documents.find_one({'_id': ObjectId(document_id)})
            if not current:
                raise DatabaseError("Document not found")

            # Prepare update data
            data['updated_at'] = datetime.utcnow()
            data['updated_by'] = user_id
            data['version'] = current.get('version', 1) + 1

            # Store previous version
            self._store_document_version(current)

            # Update document
            result = self.documents.update_one(
                {'_id': ObjectId(document_id)},
                {'$set': data}
            )

            # Log audit
            self._log_audit('document_updated', user_id, document_id, data)

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            raise DatabaseError(f"Failed to update document: {e}")

    def delete_document(self, document_id: str, user_id: str = None, soft_delete: bool = True) -> bool:
        """Delete document (soft delete by default)"""
        try:
            if soft_delete:
                # Soft delete - mark as deleted
                result = self.documents.update_one(
                    {'_id': ObjectId(document_id)},
                    {
                        '$set': {
                            'deleted': True,
                            'deleted_at': datetime.utcnow(),
                            'deleted_by': user_id
                        }
                    }
                )
            else:
                # Hard delete
                result = self.documents.delete_one({'_id': ObjectId(document_id)})

            # Log audit
            self._log_audit('document_deleted', user_id, document_id, {'soft_delete': soft_delete})

            return result.modified_count > 0 if soft_delete else result.deleted_count > 0

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise DatabaseError(f"Failed to delete document: {e}")

    def search_documents(self, query: Dict[str, Any] = None, text_search: str = None,
                        skip: int = 0, limit: int = 50, sort: List[tuple] = None) -> Dict[str, Any]:
        """Advanced document search with text search and pagination"""
        try:
            # Build query
            final_query = query or {}

            # Exclude soft-deleted documents
            final_query['$and'] = final_query.get('$and', [])
            final_query['$and'].append({'$or': [{'deleted': False}, {'deleted': {'$exists': False}}]})

            # Add text search if provided
            if text_search:
                final_query['$text'] = {'$search': text_search}

            # Get total count
            total = self.documents.count_documents(final_query)

            # Execute query
            cursor = self.documents.find(final_query)

            # Add text score for relevance if text search
            if text_search:
                cursor = cursor.sort([('score', {'$meta': 'textScore'})])
            elif sort:
                cursor = cursor.sort(sort)
            else:
                cursor = cursor.sort([('created_at', DESCENDING)])

            # Apply pagination
            cursor = cursor.skip(skip).limit(limit)

            # Convert to list
            documents = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                documents.append(doc)

            return {
                'documents': documents,
                'total': total,
                'skip': skip,
                'limit': limit
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise DatabaseError(f"Search failed: {e}")

    def _store_document_version(self, document: Dict[str, Any]):
        """Store document version for history tracking"""
        version_data = document.copy()
        version_data['_id'] = ObjectId()
        version_data['original_id'] = document['_id']
        version_data['versioned_at'] = datetime.utcnow()

        self.db['document_versions'].insert_one(version_data)

    def _log_audit(self, action: str, user_id: str, document_id: str = None, details: Dict[str, Any] = None):
        """Log audit trail"""
        audit_entry = {
            'timestamp': datetime.utcnow(),
            'action': action,
            'user_id': user_id,
            'document_id': document_id,
            'details': details or {},
            'ip_address': None  # Will be set by the application
        }

        self.audit_log.insert_one(audit_entry)

    def backup_database(self, backup_dir: str = None) -> str:
        """Secure database backup with encryption"""
        try:
            backup_dir = backup_dir or self.config.get('BACKUP', 'backup_dir', 'backups')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = Path(backup_dir) / f"backup_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)

            # Use subprocess with proper argument handling
            cmd = [
                'mongodump',
                '--host', f"{self.db_config['host']}:{self.db_config['port']}",
                '--db', self.db_config['database'],
                '--out', str(backup_path)
            ]

            # Add authentication if configured
            if self.db_config.get('username'):
                cmd.extend(['--username', self.db_config['username']])
                cmd.extend(['--password', self.db_config['password']])
                cmd.extend(['--authenticationDatabase', self.db_config.get('auth_source', 'admin')])

            # Execute backup
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Create metadata file
            metadata = {
                'timestamp': timestamp,
                'database': self.db_config['database'],
                'document_count': self.documents.count_documents({}),
                'collections': self.db.list_collection_names(),
                'backup_size': sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            }

            with open(backup_path / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2, default=str)

            # Encrypt backup if configured
            if self.config.get('BACKUP', 'encrypt_backups', 'true').lower() == 'true':
                self._encrypt_backup(backup_path)

            logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)

        except subprocess.CalledProcessError as e:
            logger.error(f"Backup failed: {e.stderr}")
            raise BackupError(f"Backup failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise BackupError(f"Backup failed: {e}")

    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            backup_path = Path(backup_path)

            if not backup_path.exists():
                raise BackupError(f"Backup path not found: {backup_path}")

            # Decrypt if needed
            if (backup_path / '.encrypted').exists():
                self._decrypt_backup(backup_path)

            # Use subprocess for restore
            cmd = [
                'mongorestore',
                '--host', f"{self.db_config['host']}:{self.db_config['port']}",
                '--db', self.db_config['database'],
                '--drop',  # Drop existing collections
                str(backup_path / self.db_config['database'])
            ]

            # Add authentication if configured
            if self.db_config.get('username'):
                cmd.extend(['--username', self.db_config['username']])
                cmd.extend(['--password', self.db_config['password']])
                cmd.extend(['--authenticationDatabase', self.db_config.get('auth_source', 'admin')])

            # Execute restore
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            logger.info(f"Database restored from: {backup_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Restore failed: {e.stderr}")
            raise BackupError(f"Restore failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise BackupError(f"Restore failed: {e}")

    def _encrypt_backup(self, backup_path: Path):
        """Encrypt backup directory"""
        # Implementation would use cryptography library
        # Placeholder for encryption logic
        (backup_path / '.encrypted').touch()

    def _decrypt_backup(self, backup_path: Path):
        """Decrypt backup directory"""
        # Implementation would use cryptography library
        # Placeholder for decryption logic
        (backup_path / '.encrypted').unlink()

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {
                'total_documents': self.documents.count_documents({}),
                'total_users': self.users.count_documents({}),
                'total_templates': self.templates.count_documents({}),
                'documents_by_type': [],
                'documents_by_status': [],
                'storage_used': self.db.command('dbStats')['dataSize'],
                'last_backup': None
            }

            # Documents by type
            pipeline = [
                {'$group': {'_id': '$jenis_dokumen', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            stats['documents_by_type'] = list(self.documents.aggregate(pipeline))

            # Documents by status
            pipeline = [
                {'$group': {'_id': '$status', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            stats['documents_by_status'] = list(self.documents.aggregate(pipeline))

            return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def close(self):
        """Close database connection"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("Database connection closed")