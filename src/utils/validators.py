"""
Input validation utilities with security focus
"""
import re
import os
from datetime import datetime
from typing import Any, List, Optional, Tuple
import mimetypes
from pathlib import Path
import hashlib
import hmac
import secrets
from urllib.parse import urlparse
import bleach

class InputValidator:
    """Comprehensive input validation class"""

    # Regular expressions for validation
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_REGEX = re.compile(r'^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$')
    ALPHANUMERIC_REGEX = re.compile(r'^[a-zA-Z0-9]+$')
    SQL_INJECTION_PATTERNS = [
        r'(\bUNION\b.*\bSELECT\b)',
        r'(\bDROP\b.*\bTABLE\b)',
        r'(\bINSERT\b.*\bINTO\b)',
        r'(\bDELETE\b.*\bFROM\b)',
        r'(\bUPDATE\b.*\bSET\b)',
        r'(--|\#|\/\*|\*\/)',
        r'(\bOR\b.*=.*)',
        r'(\bAND\b.*=.*)',
        r'(;.*\bEXEC\b)',
        r'(\bSCRIPT\b)',
        r'(<.*>)',
    ]

    @staticmethod
    def sanitize_input(value: str, allow_html: bool = False) -> str:
        """Sanitize user input to prevent XSS and injection attacks"""
        if not value:
            return ""

        # Remove null bytes
        value = value.replace('\x00', '')

        # Strip leading/trailing whitespace
        value = value.strip()

        # Check for SQL injection patterns
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError(f"Potentially malicious input detected")

        # Clean HTML if needed
        if not allow_html:
            # Remove all HTML tags
            value = bleach.clean(value, tags=[], strip=True)
        else:
            # Allow only safe HTML tags
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li']
            allowed_attrs = {}
            value = bleach.clean(value, tags=allowed_tags, attributes=allowed_attrs, strip=True)

        return value

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address format"""
        if not email or len(email) > 254:
            return False
        return bool(InputValidator.EMAIL_REGEX.match(email))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        # Remove common separators for validation
        phone_clean = re.sub(r'[\s\-\.\(\)]', '', phone)
        if len(phone_clean) < 10 or len(phone_clean) > 15:
            return False
        return bool(InputValidator.PHONE_REGEX.match(phone))

    @staticmethod
    def validate_date(date_str: str, format: str = '%Y-%m-%d') -> Tuple[bool, Optional[datetime]]:
        """Validate date string and return parsed date"""
        try:
            date_obj = datetime.strptime(date_str, format)
            return True, date_obj
        except (ValueError, TypeError):
            return False, None

    @staticmethod
    def validate_file(file_path: str, allowed_extensions: List[str] = None,
                     max_size: int = 10485760) -> Tuple[bool, str]:
        """
        Validate file for upload
        Args:
            file_path: Path to the file
            allowed_extensions: List of allowed file extensions
            max_size: Maximum file size in bytes (default 10MB)
        """
        if not os.path.exists(file_path):
            return False, "File does not exist"

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            return False, f"File size exceeds maximum allowed size ({max_size} bytes)"

        # Check file extension
        if allowed_extensions:
            file_ext = Path(file_path).suffix.lower().lstrip('.')
            if file_ext not in [ext.lower() for ext in allowed_extensions]:
                return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"

        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            # Check for potentially dangerous MIME types
            dangerous_types = ['application/x-executable', 'application/x-msdos-program']
            if mime_type in dangerous_types:
                return False, "Potentially dangerous file type detected"

        # Check for file content tampering (basic check)
        try:
            with open(file_path, 'rb') as f:
                header = f.read(512)
                # Check for common executable signatures
                if header.startswith(b'MZ') or header.startswith(b'\x7fELF'):
                    if not file_path.endswith(('.exe', '.dll', '.so')):
                        return False, "File content does not match extension"
        except:
            return False, "Unable to read file"

        return True, "File is valid"

    @staticmethod
    def validate_password(password: str, min_length: int = 8,
                         require_uppercase: bool = True,
                         require_lowercase: bool = True,
                         require_number: bool = True,
                         require_special: bool = True) -> Tuple[bool, List[str]]:
        """
        Validate password strength
        Returns: (is_valid, list_of_errors)
        """
        errors = []

        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long")

        if require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if require_number and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")

        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        # Check for common weak passwords
        weak_passwords = ['password', '12345678', 'qwerty', 'admin', 'letmein']
        if password.lower() in weak_passwords:
            errors.append("Password is too common")

        return len(errors) == 0, errors

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and safety"""
        try:
            result = urlparse(url)
            # Check if scheme and netloc are present
            if not all([result.scheme, result.netloc]):
                return False
            # Only allow http and https
            if result.scheme not in ['http', 'https']:
                return False
            # Check for local addresses (security)
            if result.netloc in ['localhost', '127.0.0.1', '0.0.0.0']:
                return False
            return True
        except:
            return False

    @staticmethod
    def validate_json(json_str: str) -> Tuple[bool, Any]:
        """Validate JSON string"""
        import json
        try:
            data = json.loads(json_str)
            return True, data
        except (json.JSONDecodeError, TypeError):
            return False, None

    @staticmethod
    def validate_field_length(value: str, min_length: int = 0,
                            max_length: int = 255) -> bool:
        """Validate field length"""
        if not value:
            return min_length == 0
        return min_length <= len(value) <= max_length

    @staticmethod
    def validate_number(value: str, min_val: float = None,
                       max_val: float = None) -> Tuple[bool, Optional[float]]:
        """Validate numeric input"""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False, None
            if max_val is not None and num > max_val:
                return False, None
            return True, num
        except (ValueError, TypeError):
            return False, None

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> Tuple[str, str]:
        """
        Hash password using PBKDF2
        Returns: (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(32)

        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # iterations
        )

        return key.hex(), salt.hex()

    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash"""
        salt_bytes = bytes.fromhex(salt)
        new_hash, _ = InputValidator.hash_password(password, salt_bytes)
        return hmac.compare_digest(new_hash, hashed)

    @staticmethod
    def validate_csrf_token(token: str, session_token: str) -> bool:
        """Validate CSRF token"""
        return hmac.compare_digest(token, session_token)

class DocumentValidator:
    """Validator specific to document fields"""

    @staticmethod
    def validate_document_number(number: str) -> bool:
        """Validate document number format"""
        # Format: XXX/YYY/2024 or similar
        pattern = r'^[A-Z0-9]+\/[A-Z0-9]+\/\d{4}$'
        return bool(re.match(pattern, number))

    @staticmethod
    def validate_document_type(doc_type: str, allowed_types: List[str]) -> bool:
        """Validate document type against allowed list"""
        return doc_type in allowed_types

    @staticmethod
    def validate_disposition_data(data: dict) -> Tuple[bool, List[str]]:
        """Validate complete disposition data"""
        errors = []
        required_fields = ['nomor_surat', 'tanggal_surat', 'jenis_dokumen', 'perihal']

        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Field '{field}' is required")

        # Validate specific fields
        if 'nomor_surat' in data and data['nomor_surat']:
            if not DocumentValidator.validate_document_number(data['nomor_surat']):
                errors.append("Invalid document number format")

        if 'tanggal_surat' in data and data['tanggal_surat']:
            valid, _ = InputValidator.validate_date(data['tanggal_surat'])
            if not valid:
                errors.append("Invalid date format")

        if 'email' in data and data['email']:
            if not InputValidator.validate_email(data['email']):
                errors.append("Invalid email format")

        return len(errors) == 0, errors