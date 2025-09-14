"""
Configuration management module with security enhancements
"""
import configparser
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from cryptography.fernet import Fernet
import hashlib

logger = logging.getLogger(__name__)

class ConfigManager:
    """Enhanced configuration manager with encryption support"""

    def __init__(self, config_file: str = 'config.ini'):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.config_dir = Path('config')
        self.config_dir.mkdir(exist_ok=True)
        self.config_path = self.config_dir / config_file
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)

        if not self.config_path.exists():
            self.create_default_config()
        self.load_config()

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        key_file = self.config_dir / '.key'
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions on key file
            os.chmod(key_file, 0o600)
            return key

    def create_default_config(self):
        """Create default configuration with security settings"""
        self.config['DATABASE'] = {
            'host': 'localhost',
            'port': '27017',
            'database': 'disposisi',
            'use_ssl': 'false',
            'auth_source': 'admin'
        }

        self.config['SECURITY'] = {
            'session_timeout': '3600',  # 1 hour
            'max_login_attempts': '5',
            'password_min_length': '8',
            'require_special_char': 'true',
            'require_uppercase': 'true',
            'require_number': 'true',
            'enable_2fa': 'false'
        }

        self.config['APPLICATION'] = {
            'theme': 'darkly',
            'language': 'id',
            'items_per_page': '50',
            'auto_backup': 'true',
            'backup_interval': '86400',  # 24 hours
            'max_file_size': '10485760',  # 10MB
            'allowed_file_types': 'pdf,jpg,jpeg,png,doc,docx,xls,xlsx',
            'enable_notifications': 'true',
            'enable_audit_log': 'true'
        }

        self.config['EMAIL'] = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': '587',
            'use_tls': 'true',
            'sender_email': '',
            'sender_password': ''  # Will be encrypted
        }

        self.config['API'] = {
            'enable_api': 'false',
            'api_port': '5000',
            'api_key': '',  # Will be generated
            'rate_limit': '100',  # requests per minute
            'enable_cors': 'false'
        }

        self.config['BACKUP'] = {
            'backup_dir': 'backups',
            'max_backups': '30',
            'enable_cloud_backup': 'false',
            'cloud_provider': 'none',  # google_drive, dropbox, aws_s3
            'encrypt_backups': 'true'
        }

        self.save_config()

    def load_config(self):
        """Load configuration from file"""
        try:
            self.config.read(self.config_path)
            logger.info(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as configfile:
                self.config.write(configfile)
            # Set restrictive permissions
            os.chmod(self.config_path, 0o600)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get configuration value with fallback"""
        try:
            value = self.config.get(section, key)
            # Decrypt sensitive fields
            if self._is_sensitive_field(section, key) and value:
                try:
                    value = self.cipher.decrypt(value.encode()).decode()
                except:
                    pass  # Value might not be encrypted yet
            return value
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def set(self, section: str, key: str, value: Any):
        """Set configuration value with encryption for sensitive data"""
        if section not in self.config:
            self.config[section] = {}

        # Encrypt sensitive fields
        if self._is_sensitive_field(section, key):
            value = self.cipher.encrypt(str(value).encode()).decode()

        self.config[section][key] = str(value)
        self.save_config()

    def _is_sensitive_field(self, section: str, key: str) -> bool:
        """Check if a field should be encrypted"""
        sensitive_fields = [
            ('EMAIL', 'sender_password'),
            ('DATABASE', 'password'),
            ('API', 'api_key'),
            ('BACKUP', 'cloud_api_key')
        ]
        return (section, key) in sensitive_fields

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'host': self.get('DATABASE', 'host', 'localhost'),
            'port': int(self.get('DATABASE', 'port', 27017)),
            'database': self.get('DATABASE', 'database', 'disposisi'),
            'use_ssl': self.get('DATABASE', 'use_ssl', 'false').lower() == 'true',
            'auth_source': self.get('DATABASE', 'auth_source', 'admin'),
            'username': self.get('DATABASE', 'username'),
            'password': self.get('DATABASE', 'password')
        }

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'session_timeout': int(self.get('SECURITY', 'session_timeout', 3600)),
            'max_login_attempts': int(self.get('SECURITY', 'max_login_attempts', 5)),
            'password_min_length': int(self.get('SECURITY', 'password_min_length', 8)),
            'require_special_char': self.get('SECURITY', 'require_special_char', 'true').lower() == 'true',
            'require_uppercase': self.get('SECURITY', 'require_uppercase', 'true').lower() == 'true',
            'require_number': self.get('SECURITY', 'require_number', 'true').lower() == 'true',
            'enable_2fa': self.get('SECURITY', 'enable_2fa', 'false').lower() == 'true'
        }

    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        import secrets
        api_key = secrets.token_urlsafe(32)
        self.set('API', 'api_key', api_key)
        return api_key

    def validate_config(self) -> bool:
        """Validate configuration settings"""
        try:
            # Check database connection
            db_config = self.get_database_config()
            if not db_config['host'] or not db_config['port']:
                logger.error("Invalid database configuration")
                return False

            # Check file size limits
            max_file_size = int(self.get('APPLICATION', 'max_file_size', 10485760))
            if max_file_size < 1024:  # At least 1KB
                logger.error("Invalid max file size")
                return False

            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False