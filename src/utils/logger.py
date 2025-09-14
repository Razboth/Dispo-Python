"""
Logging configuration and utilities
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
import json
from typing import Any, Dict

class CustomJSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id

        if hasattr(record, 'document_id'):
            log_obj['document_id'] = record.document_id

        if hasattr(record, 'action'):
            log_obj['action'] = record.action

        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

class AuditLogger:
    """Specialized logger for audit trail"""

    def __init__(self, log_dir: str = 'logs/audit'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """Setup audit logger with rotation"""
        logger = logging.getLogger('audit')
        logger.setLevel(logging.INFO)

        # Remove existing handlers
        logger.handlers = []

        # File handler with rotation
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.log_dir / 'audit.log',
            when='midnight',
            interval=1,
            backupCount=90,  # Keep 90 days of audit logs
            encoding='utf-8'
        )
        handler.setFormatter(CustomJSONFormatter())
        logger.addHandler(handler)

        return logger

    def log_action(self, action: str, user_id: str, document_id: str = None,
                   details: Dict[str, Any] = None, ip_address: str = None):
        """Log an audit action"""
        extra = {
            'action': action,
            'user_id': user_id,
            'ip_address': ip_address
        }

        if document_id:
            extra['document_id'] = document_id

        message = f"User {user_id} performed action: {action}"
        if details:
            message += f" - Details: {json.dumps(details)}"

        self.logger.info(message, extra=extra)

def setup_logging(config: Dict[str, Any] = None):
    """Setup application-wide logging configuration"""
    config = config or {}

    # Create logs directory
    log_dir = Path(config.get('log_dir', 'logs'))
    log_dir.mkdir(exist_ok=True)

    # Set logging level
    log_level = config.get('log_level', 'INFO')
    logging.basicConfig(level=getattr(logging, log_level))

    # Remove default handler
    logging.getLogger().handlers = []

    # Console handler with colored output
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logging.getLogger().addHandler(console_handler)

    # File handler for general application logs
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'application.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logging.getLogger().addHandler(file_handler)

    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'errors.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    logging.getLogger().addHandler(error_handler)

    # Performance logger
    perf_logger = logging.getLogger('performance')
    perf_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'performance.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    perf_handler.setFormatter(CustomJSONFormatter())
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)

    logging.info("Logging system initialized")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

class LogContext:
    """Context manager for adding context to log records"""

    def __init__(self, **kwargs):
        self.context = kwargs
        self.old_factory = None

    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)