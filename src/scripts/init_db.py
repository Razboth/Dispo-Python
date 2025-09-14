#!/usr/bin/env python3
"""
Database initialization script for Dispo-Python
This script sets up the MongoDB database with necessary collections and initial data
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pymongo import MongoClient, ASCENDING, TEXT
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database(host='localhost', port=27017, db_name='disposisi'):
    """Initialize MongoDB database with collections and indexes"""

    try:
        # Connect to MongoDB
        logger.info(f"Connecting to MongoDB at {host}:{port}")
        client = MongoClient(host=host, port=port, serverSelectionTimeoutMS=5000)

        # Test connection
        client.admin.command('ping')
        logger.info("✅ MongoDB connection successful")

        # Create or get database
        db = client[db_name]
        logger.info(f"Using database: {db_name}")

        # Create collections
        collections = [
            'documents',
            'users',
            'templates',
            'audit_log',
            'counters',
            'notifications',
            'workflow',
            'document_versions',
            'fs.files',
            'fs.chunks'
        ]

        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
            else:
                logger.info(f"Collection already exists: {collection_name}")

        # Create indexes for documents collection
        logger.info("Creating indexes for documents collection...")
        documents = db['documents']

        # Single field indexes
        documents.create_index([('nomor_surat', ASCENDING)])
        documents.create_index([('tanggal_surat', ASCENDING)])
        documents.create_index([('jenis_dokumen', ASCENDING)])
        documents.create_index([('status', ASCENDING)])
        documents.create_index([('created_at', ASCENDING)])

        # Text index for search
        documents.create_index([
            ('nomor_surat', TEXT),
            ('perihal', TEXT),
            ('asal_surat', TEXT)
        ])

        # Compound index for filtering
        documents.create_index([
            ('jenis_dokumen', ASCENDING),
            ('status', ASCENDING),
            ('tanggal_surat', ASCENDING)
        ])

        logger.info("✅ Document indexes created")

        # Create indexes for users collection
        logger.info("Creating indexes for users collection...")
        users = db['users']
        users.create_index([('username', ASCENDING)], unique=True)
        users.create_index([('email', ASCENDING)], unique=True)
        users.create_index([('status', ASCENDING)])
        users.create_index([('role', ASCENDING)])
        logger.info("✅ User indexes created")

        # Create indexes for audit_log collection
        logger.info("Creating indexes for audit_log collection...")
        audit_log = db['audit_log']
        audit_log.create_index([('timestamp', ASCENDING)])
        audit_log.create_index([('user_id', ASCENDING)])
        audit_log.create_index([('action', ASCENDING)])
        audit_log.create_index([('document_id', ASCENDING)])
        logger.info("✅ Audit log indexes created")

        # Initialize counters collection
        logger.info("Initializing counters...")
        counters = db['counters']

        # Initialize document number counter if not exists
        if counters.count_documents({'_id': 'document_number'}) == 0:
            counters.insert_one({
                '_id': 'document_number',
                'sequence_value': 1000
            })
            logger.info("Document number counter initialized at 1000")

        # Initialize user id counter if not exists
        if counters.count_documents({'_id': 'user_id'}) == 0:
            counters.insert_one({
                '_id': 'user_id',
                'sequence_value': 1
            })
            logger.info("User ID counter initialized at 1")

        # Create default templates
        logger.info("Creating default templates...")
        templates = db['templates']

        default_templates = [
            {
                'name': 'Surat Masuk',
                'fields': {
                    'jenis_dokumen': 'Surat Masuk',
                    'sifat_surat': 'Biasa',
                    'klasifikasi': 'Umum'
                },
                'created_at': datetime.utcnow()
            },
            {
                'name': 'Surat Keluar',
                'fields': {
                    'jenis_dokumen': 'Surat Keluar',
                    'sifat_surat': 'Biasa',
                    'klasifikasi': 'Umum'
                },
                'created_at': datetime.utcnow()
            },
            {
                'name': 'Nota Dinas',
                'fields': {
                    'jenis_dokumen': 'Nota Dinas',
                    'sifat_surat': 'Segera',
                    'klasifikasi': 'Internal'
                },
                'created_at': datetime.utcnow()
            }
        ]

        for template in default_templates:
            if templates.count_documents({'name': template['name']}) == 0:
                templates.insert_one(template)
                logger.info(f"Created template: {template['name']}")

        # Create sample admin user (you should change the password)
        logger.info("Checking for admin user...")
        if users.count_documents({'username': 'admin'}) == 0:
            from src.models.user import User, UserRole
            user_model = User(users)

            try:
                admin_id = user_model.create_user(
                    username='admin',
                    email='admin@disposisi.local',
                    password='Admin@123',  # Change this password!
                    full_name='System Administrator',
                    role=UserRole.ADMIN,
                    department='IT'
                )
                logger.info(f"✅ Admin user created with ID: {admin_id}")
                logger.warning("⚠️  Default admin password is 'Admin@123' - Please change it!")
            except Exception as e:
                logger.warning(f"Could not create admin user: {e}")
        else:
            logger.info("Admin user already exists")

        # Database statistics
        logger.info("\n" + "="*50)
        logger.info("Database Initialization Complete!")
        logger.info("="*50)
        logger.info(f"Database: {db_name}")
        logger.info(f"Collections: {len(db.list_collection_names())}")
        logger.info(f"Documents: {documents.count_documents({})}")
        logger.info(f"Users: {users.count_documents({})}")
        logger.info(f"Templates: {templates.count_documents({})}")
        logger.info("="*50)

        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def check_mongodb_status():
    """Check if MongoDB is running and accessible"""
    try:
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        version = client.server_info()['version']
        logger.info(f"✅ MongoDB is running (version {version})")
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB is not accessible: {e}")
        logger.info("\nTo start MongoDB:")
        logger.info("  macOS: brew services start mongodb-community")
        logger.info("  Linux: sudo systemctl start mongod")
        logger.info("  Windows: net start MongoDB")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Initialize Dispo-Python database')
    parser.add_argument('--host', default='localhost', help='MongoDB host')
    parser.add_argument('--port', type=int, default=27017, help='MongoDB port')
    parser.add_argument('--database', default='disposisi', help='Database name')
    parser.add_argument('--check-only', action='store_true', help='Only check MongoDB status')

    args = parser.parse_args()

    if args.check_only:
        check_mongodb_status()
    else:
        if check_mongodb_status():
            initialize_database(
                host=args.host,
                port=args.port,
                db_name=args.database
            )
        else:
            logger.error("Please start MongoDB first before initializing the database")
            sys.exit(1)