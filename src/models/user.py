"""
User model with authentication and authorization
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import secrets
import pyotp
from bson.objectid import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
import logging

from ..utils.validators import InputValidator
from ..utils.exceptions import AuthenticationError, ValidationError

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles enumeration"""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"

class UserStatus(Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    SUSPENDED = "suspended"

class Permission(Enum):
    """System permissions"""
    # Document permissions
    DOCUMENT_CREATE = "document.create"
    DOCUMENT_READ = "document.read"
    DOCUMENT_UPDATE = "document.update"
    DOCUMENT_DELETE = "document.delete"
    DOCUMENT_APPROVE = "document.approve"
    DOCUMENT_EXPORT = "document.export"

    # User management permissions
    USER_CREATE = "user.create"
    USER_READ = "user.read"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"

    # System permissions
    SYSTEM_CONFIG = "system.config"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"
    SYSTEM_AUDIT = "system.audit"

    # Report permissions
    REPORT_VIEW = "report.view"
    REPORT_CREATE = "report.create"
    REPORT_EXPORT = "report.export"

class User:
    """User model with authentication features"""

    # Role-based permissions mapping
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [p.value for p in Permission],  # All permissions
        UserRole.MANAGER: [
            Permission.DOCUMENT_CREATE.value,
            Permission.DOCUMENT_READ.value,
            Permission.DOCUMENT_UPDATE.value,
            Permission.DOCUMENT_DELETE.value,
            Permission.DOCUMENT_APPROVE.value,
            Permission.DOCUMENT_EXPORT.value,
            Permission.USER_READ.value,
            Permission.REPORT_VIEW.value,
            Permission.REPORT_CREATE.value,
            Permission.REPORT_EXPORT.value,
        ],
        UserRole.USER: [
            Permission.DOCUMENT_CREATE.value,
            Permission.DOCUMENT_READ.value,
            Permission.DOCUMENT_UPDATE.value,
            Permission.DOCUMENT_EXPORT.value,
            Permission.REPORT_VIEW.value,
        ],
        UserRole.VIEWER: [
            Permission.DOCUMENT_READ.value,
            Permission.REPORT_VIEW.value,
        ]
    }

    def __init__(self, collection: Collection):
        self.collection = collection
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create necessary indexes"""
        self.collection.create_index("username", unique=True)
        self.collection.create_index("email", unique=True)
        self.collection.create_index("status")
        self.collection.create_index("role")
        self.collection.create_index("last_login")

    def create_user(self, username: str, email: str, password: str,
                   full_name: str, role: UserRole = UserRole.USER,
                   department: str = None) -> str:
        """Create a new user"""
        # Validate inputs
        if not InputValidator.validate_email(email):
            raise ValidationError("Invalid email format")

        valid, errors = InputValidator.validate_password(password)
        if not valid:
            raise ValidationError(f"Password validation failed: {', '.join(errors)}")

        # Hash password
        hashed_password, salt = InputValidator.hash_password(password)

        # Generate 2FA secret
        totp_secret = pyotp.random_base32()

        user_data = {
            "username": username.lower(),
            "email": email.lower(),
            "password": hashed_password,
            "salt": salt,
            "full_name": full_name,
            "role": role.value,
            "department": department,
            "status": UserStatus.ACTIVE.value,
            "permissions": self.ROLE_PERMISSIONS[role],
            "totp_secret": totp_secret,
            "totp_enabled": False,
            "failed_login_attempts": 0,
            "last_failed_login": None,
            "password_changed_at": datetime.utcnow(),
            "must_change_password": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": None,  # Will be set by the system
            "last_login": None,
            "last_login_ip": None,
            "session_tokens": [],
            "preferences": {
                "theme": "darkly",
                "language": "id",
                "notifications_enabled": True,
                "items_per_page": 50
            }
        }

        try:
            result = self.collection.insert_one(user_data)
            logger.info(f"User created: {username}")
            return str(result.inserted_id)
        except DuplicateKeyError:
            raise ValidationError("Username or email already exists")

    def authenticate(self, username: str, password: str, ip_address: str = None) -> Dict[str, Any]:
        """Authenticate user and return user data with session token"""
        user = self.collection.find_one({
            "$or": [
                {"username": username.lower()},
                {"email": username.lower()}
            ]
        })

        if not user:
            logger.warning(f"Authentication failed: User not found - {username}")
            raise AuthenticationError("Invalid credentials")

        # Check account status
        if user['status'] == UserStatus.LOCKED.value:
            raise AuthenticationError("Account is locked")
        elif user['status'] == UserStatus.SUSPENDED.value:
            raise AuthenticationError("Account is suspended")
        elif user['status'] == UserStatus.INACTIVE.value:
            raise AuthenticationError("Account is inactive")

        # Verify password
        if not InputValidator.verify_password(password, user['password'], user['salt']):
            # Increment failed login attempts
            self.collection.update_one(
                {"_id": user['_id']},
                {
                    "$inc": {"failed_login_attempts": 1},
                    "$set": {"last_failed_login": datetime.utcnow()}
                }
            )

            # Lock account after 5 failed attempts
            if user['failed_login_attempts'] >= 4:
                self.collection.update_one(
                    {"_id": user['_id']},
                    {"$set": {"status": UserStatus.LOCKED.value}}
                )
                logger.warning(f"Account locked due to failed attempts: {username}")
                raise AuthenticationError("Account locked due to multiple failed attempts")

            raise AuthenticationError("Invalid credentials")

        # Generate session token
        session_token = secrets.token_urlsafe(32)
        session_data = {
            "token": session_token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "ip_address": ip_address
        }

        # Update user login info
        self.collection.update_one(
            {"_id": user['_id']},
            {
                "$set": {
                    "last_login": datetime.utcnow(),
                    "last_login_ip": ip_address,
                    "failed_login_attempts": 0,
                    "last_failed_login": None
                },
                "$push": {
                    "session_tokens": {
                        "$each": [session_data],
                        "$slice": -10  # Keep only last 10 sessions
                    }
                }
            }
        )

        logger.info(f"User authenticated: {username}")

        return {
            "user_id": str(user['_id']),
            "username": user['username'],
            "full_name": user['full_name'],
            "email": user['email'],
            "role": user['role'],
            "permissions": user['permissions'],
            "session_token": session_token,
            "totp_enabled": user.get('totp_enabled', False),
            "must_change_password": user.get('must_change_password', False)
        }

    def verify_session(self, user_id: str, session_token: str) -> Optional[Dict[str, Any]]:
        """Verify session token and return user data"""
        try:
            user = self.collection.find_one({
                "_id": ObjectId(user_id),
                "session_tokens.token": session_token,
                "session_tokens.expires_at": {"$gt": datetime.utcnow()}
            })

            if not user:
                return None

            return {
                "user_id": str(user['_id']),
                "username": user['username'],
                "full_name": user['full_name'],
                "role": user['role'],
                "permissions": user['permissions']
            }
        except:
            return None

    def logout(self, user_id: str, session_token: str):
        """Logout user by removing session token"""
        self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"session_tokens": {"token": session_token}}}
        )
        logger.info(f"User logged out: {user_id}")

    def change_password(self, user_id: str, old_password: str, new_password: str):
        """Change user password"""
        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValidationError("User not found")

        # Verify old password
        if not InputValidator.verify_password(old_password, user['password'], user['salt']):
            raise AuthenticationError("Current password is incorrect")

        # Validate new password
        valid, errors = InputValidator.validate_password(new_password)
        if not valid:
            raise ValidationError(f"Password validation failed: {', '.join(errors)}")

        # Hash new password
        hashed_password, salt = InputValidator.hash_password(new_password)

        # Update password
        self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "password": hashed_password,
                    "salt": salt,
                    "password_changed_at": datetime.utcnow(),
                    "must_change_password": False,
                    "updated_at": datetime.utcnow()
                },
                "$unset": {"session_tokens": 1}  # Invalidate all sessions
            }
        )
        logger.info(f"Password changed for user: {user_id}")

    def reset_password(self, user_id: str, new_password: str):
        """Admin reset of user password"""
        # Validate new password
        valid, errors = InputValidator.validate_password(new_password)
        if not valid:
            raise ValidationError(f"Password validation failed: {', '.join(errors)}")

        # Hash new password
        hashed_password, salt = InputValidator.hash_password(new_password)

        # Update password
        self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "password": hashed_password,
                    "salt": salt,
                    "password_changed_at": datetime.utcnow(),
                    "must_change_password": True,
                    "updated_at": datetime.utcnow()
                },
                "$unset": {"session_tokens": 1}
            }
        )
        logger.info(f"Password reset for user: {user_id}")

    def enable_2fa(self, user_id: str) -> str:
        """Enable 2FA for user and return QR code URI"""
        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValidationError("User not found")

        totp = pyotp.TOTP(user['totp_secret'])
        provisioning_uri = totp.provisioning_uri(
            name=user['email'],
            issuer_name='Disposisi System'
        )

        self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"totp_enabled": True}}
        )

        return provisioning_uri

    def verify_2fa(self, user_id: str, token: str) -> bool:
        """Verify 2FA token"""
        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get('totp_enabled'):
            return False

        totp = pyotp.TOTP(user['totp_secret'])
        return totp.verify(token, valid_window=1)

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return False
        return permission in user.get('permissions', [])

    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update user preferences"""
        self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"preferences": preferences, "updated_at": datetime.utcnow()}}
        )

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user['_id'] = str(user['_id'])
            # Remove sensitive fields
            user.pop('password', None)
            user.pop('salt', None)
            user.pop('totp_secret', None)
            user.pop('session_tokens', None)
        return user

    def list_users(self, filters: Dict[str, Any] = None, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """List users with filters"""
        query = filters or {}
        users = self.collection.find(query).skip(skip).limit(limit)

        result = []
        for user in users:
            user['_id'] = str(user['_id'])
            # Remove sensitive fields
            user.pop('password', None)
            user.pop('salt', None)
            user.pop('totp_secret', None)
            user.pop('session_tokens', None)
            result.append(user)

        return result