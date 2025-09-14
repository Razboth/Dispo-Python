#!/usr/bin/env python3
"""
Dispo-TI Application - Main Entry Point
Enhanced Document Management System with Security and Modern Features
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import ConfigManager
from src.utils.logger import setup_logging, get_logger
from src.models.database import DatabaseManager
from src.views.main_window import MainApplication
from src.services.scheduler import BackupScheduler
from src.utils.exceptions import ConfigurationError, DatabaseError

# Set up logging
setup_logging()
logger = get_logger(__name__)

class DisposisiApplication:
    """Main application controller"""

    def __init__(self, config_file: str = None):
        """Initialize the application"""
        self.config = None
        self.db = None
        self.scheduler = None

        try:
            # Load configuration
            self.config = ConfigManager(config_file or 'config.ini')

            # Validate configuration
            if not self.config.validate_config():
                raise ConfigurationError("Invalid configuration")

            # Initialize database
            self.db = DatabaseManager(self.config)

            # Initialize scheduler for automated tasks
            self.scheduler = BackupScheduler(self.config, self.db)

            logger.info("Application initialized successfully")

        except Exception as e:
            logger.error(f"Application initialization failed: {e}")
            raise

    def run_gui(self):
        """Run the GUI application"""
        try:
            logger.info("Starting GUI application")

            # Start scheduler in background
            if self.scheduler:
                self.scheduler.start()

            # Create and run main window
            app = MainApplication(self.config, self.db)
            app.run()

        except Exception as e:
            logger.error(f"GUI application error: {e}")
            raise
        finally:
            self.cleanup()

    def run_api(self, host: str = "0.0.0.0", port: int = 5000):
        """Run the API server"""
        try:
            logger.info(f"Starting API server on {host}:{port}")

            # Import API app
            from src.api.main import app
            import uvicorn

            # Configure API with database
            app.state.db = self.db
            app.state.config = self.config

            # Start scheduler
            if self.scheduler:
                self.scheduler.start()

            # Run API server
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )

        except Exception as e:
            logger.error(f"API server error: {e}")
            raise
        finally:
            self.cleanup()

    def run_cli(self, args):
        """Run CLI commands"""
        try:
            if args.command == 'backup':
                self.backup_database()
            elif args.command == 'restore':
                self.restore_database(args.backup_path)
            elif args.command == 'init':
                self.initialize_database()
            elif args.command == 'migrate':
                self.migrate_database()
            elif args.command == 'stats':
                self.show_statistics()
            elif args.command == 'user':
                self.manage_user(args)
            else:
                logger.error(f"Unknown command: {args.command}")

        except Exception as e:
            logger.error(f"CLI error: {e}")
            raise

    def backup_database(self):
        """Perform database backup"""
        try:
            backup_path = self.db.backup_database()
            logger.info(f"Backup completed: {backup_path}")
            print(f"✓ Database backed up to: {backup_path}")
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            print(f"✗ Backup failed: {e}")

    def restore_database(self, backup_path: str):
        """Restore database from backup"""
        try:
            if self.db.restore_database(backup_path):
                logger.info(f"Database restored from: {backup_path}")
                print(f"✓ Database restored from: {backup_path}")
            else:
                print("✗ Restore failed")
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            print(f"✗ Restore failed: {e}")

    def initialize_database(self):
        """Initialize database with default data"""
        try:
            from src.scripts.init_db import initialize_database
            initialize_database(self.db, self.config)
            print("✓ Database initialized successfully")
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            print(f"✗ Initialization failed: {e}")

    def migrate_database(self):
        """Run database migrations"""
        try:
            from src.scripts.migrations import run_migrations
            run_migrations(self.db)
            print("✓ Migrations completed successfully")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            print(f"✗ Migration failed: {e}")

    def show_statistics(self):
        """Show database statistics"""
        try:
            stats = self.db.get_statistics()
            print("\n📊 Database Statistics")
            print("=" * 40)
            print(f"Total Documents: {stats.get('total_documents', 0)}")
            print(f"Total Users: {stats.get('total_users', 0)}")
            print(f"Total Templates: {stats.get('total_templates', 0)}")
            print(f"Storage Used: {stats.get('storage_used', 0) / 1024 / 1024:.2f} MB")

            if stats.get('documents_by_type'):
                print("\n📑 Documents by Type:")
                for item in stats['documents_by_type']:
                    print(f"  - {item['_id']}: {item['count']}")

            if stats.get('documents_by_status'):
                print("\n📋 Documents by Status:")
                for item in stats['documents_by_status']:
                    print(f"  - {item['_id']}: {item['count']}")

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            print(f"✗ Failed to get statistics: {e}")

    def manage_user(self, args):
        """User management commands"""
        from src.models.user import User, UserRole

        user_model = User(self.db.users)

        if args.action == 'create':
            try:
                user_id = user_model.create_user(
                    username=args.username,
                    email=args.email,
                    password=args.password,
                    full_name=args.full_name,
                    role=UserRole[args.role.upper()],
                    department=args.department
                )
                print(f"✓ User created with ID: {user_id}")
            except Exception as e:
                print(f"✗ Failed to create user: {e}")

        elif args.action == 'list':
            users = user_model.list_users()
            print("\n👥 Users:")
            print("=" * 60)
            for user in users:
                print(f"Username: {user['username']}")
                print(f"  Name: {user['full_name']}")
                print(f"  Email: {user['email']}")
                print(f"  Role: {user['role']}")
                print(f"  Status: {user['status']}")
                print("-" * 60)

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.scheduler:
                self.scheduler.stop()
            if self.db:
                self.db.close()
            logger.info("Application cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Dispo-TI Document Management System')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--mode', choices=['gui', 'api', 'cli'], default='gui',
                       help='Application mode')

    # API options
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='API server host')
    parser.add_argument('--port', type=int, default=5000,
                       help='API server port')

    # CLI commands
    subparsers = parser.add_subparsers(dest='command', help='CLI commands')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup database')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore database')
    restore_parser.add_argument('backup_path', help='Path to backup')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize database')

    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run migrations')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')

    # User management
    user_parser = subparsers.add_parser('user', help='User management')
    user_parser.add_argument('action', choices=['create', 'list'],
                            help='User action')
    user_parser.add_argument('--username', help='Username')
    user_parser.add_argument('--email', help='Email')
    user_parser.add_argument('--password', help='Password')
    user_parser.add_argument('--full-name', dest='full_name', help='Full name')
    user_parser.add_argument('--role', choices=['admin', 'manager', 'user', 'viewer'],
                            default='user', help='User role')
    user_parser.add_argument('--department', help='Department')

    args = parser.parse_args()

    try:
        # Create application instance
        app = DisposisiApplication(args.config)

        # Run based on mode
        if args.mode == 'gui':
            app.run_gui()
        elif args.mode == 'api':
            app.run_api(args.host, args.port)
        elif args.mode == 'cli':
            if not args.command:
                parser.print_help()
            else:
                app.run_cli(args)
        else:
            parser.print_help()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()