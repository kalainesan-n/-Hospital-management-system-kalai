"""
Authentication and Authorization Service.
Handles password hashing with salt, authentication verification, and session state.
"""

import hashlib
import os
import secrets
from typing import Optional, Dict, Any, Tuple
from database.connection import Database

class AuthService:
    """Provides secure administrative authentication and password management."""

    _current_user: Optional[Dict[str, Any]] = None

    @staticmethod
    def generate_salt(length: int = 32) -> str:
        """Generates a cryptographically secure random hexadecimal salt."""
        return secrets.token_hex(length // 2)

    @classmethod
    def hash_password(cls, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hashes a password with a salt using SHA-256 with key stretching.
        Returns (hash_string, salt_string).
        """
        if not salt:
            salt = cls.generate_salt()
        # SHA-256 with 100,000 iterations for defense against brute force
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations=100000
        ).hex()
        return pwd_hash, salt

    @classmethod
    def verify_password(cls, password: str, stored_hash: str, salt: str) -> bool:
        """Verifies a plain password against the stored hash and salt."""
        computed_hash, _ = cls.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, stored_hash)

    @classmethod
    def login(cls, username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticates an admin user against the MySQL database.
        Returns (success_bool, message, user_dict_or_none).
        """
        username = username.strip()
        if not username or not password:
            return False, "Username and password cannot be empty.", None

        try:
            with Database() as db:
                query = "SELECT admin_id, username, password_hash, salt, full_name, email, role FROM admins WHERE username = %s"
                user = db.execute_one(query, (username,))

                if not user:
                    return False, "Invalid username or password.", None

                if cls.verify_password(password, user['password_hash'], user['salt']):
                    # Remove sensitive fields from memory
                    del user['password_hash']
                    del user['salt']
                    cls._current_user = user

                    # Log successful login
                    db.execute_non_query(
                        "INSERT INTO activity_logs (action, entity_type, entity_id, details, performed_by) VALUES (%s, %s, %s, %s, %s)",
                        ("LOGIN_SUCCESS", "Admin", str(user['admin_id']), f"User '{username}' logged in successfully.", username)
                    )
                    return True, "Login successful.", user
                else:
                    return False, "Invalid username or password.", None
        except Exception as e:
            return False, f"Authentication error: {str(e)}", None

    @classmethod
    def logout(cls):
        """Logs out the currently active admin."""
        if cls._current_user:
            try:
                with Database() as db:
                    db.execute_non_query(
                        "INSERT INTO activity_logs (action, entity_type, entity_id, details, performed_by) VALUES (%s, %s, %s, %s, %s)",
                        ("LOGOUT", "Admin", str(cls._current_user.get('admin_id', 0)), f"User '{cls._current_user.get('username')}' logged out.", cls._current_user.get('username', 'admin'))
                    )
            except Exception:
                pass
        cls._current_user = None

    @classmethod
    def get_current_user(cls) -> Optional[Dict[str, Any]]:
        """Returns the currently logged-in user or None."""
        return cls._current_user

    @classmethod
    def is_authenticated(cls) -> bool:
        """Checks if a session is currently active."""
        return cls._current_user is not None
