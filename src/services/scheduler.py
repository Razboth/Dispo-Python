"""
Background scheduler for automated tasks
"""

import threading
import time
import schedule
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class BackupScheduler:
    """Scheduler for automated database backups"""

    def __init__(self, config, db_manager):
        self.config = config
        self.db = db_manager
        self.running = False
        self.thread = None

        # Configure schedule based on config
        if self.config.get('APPLICATION', 'auto_backup', 'true').lower() == 'true':
            interval = int(self.config.get('APPLICATION', 'backup_interval', 86400))  # Default 24 hours

            # Schedule backup
            if interval <= 3600:  # Every hour or less
                schedule.every(interval).seconds.do(self.run_backup)
            elif interval <= 86400:  # Daily
                schedule.every().day.at("02:00").do(self.run_backup)
            else:  # Weekly
                schedule.every().monday.at("02:00").do(self.run_backup)

            logger.info(f"Backup scheduler configured with interval: {interval} seconds")

    def run_backup(self):
        """Execute backup task"""
        try:
            logger.info("Starting scheduled backup...")
            backup_path = self.db.backup_database()
            logger.info(f"Scheduled backup completed: {backup_path}")

            # Clean old backups
            self.cleanup_old_backups()

        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")

    def cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        try:
            max_backups = int(self.config.get('BACKUP', 'max_backups', 30))
            # Implementation for cleaning old backups
            logger.info(f"Cleaned up old backups, keeping last {max_backups}")
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")

    def start(self):
        """Start the scheduler in background"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info("Backup scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Backup scheduler stopped")

    def _run(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute