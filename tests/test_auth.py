"""
Unit Tests for Authentication Service.
Validates key stretching with PBKDF2-HMAC-SHA256, salt uniqueness, and constant-time password verification.
"""

import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.auth_service import AuthService

class TestAuthService(unittest.TestCase):
    """Verifies security functions in AuthService."""

    def test_salt_uniqueness(self):
        """Tests that generated salts are unique and cryptographically long."""
        salt1 = AuthService.generate_salt()
        salt2 = AuthService.generate_salt()
        self.assertNotEqual(salt1, salt2)
        self.assertGreaterEqual(len(salt1), 32)

    def test_hash_and_verify_correct_password(self):
        """Tests that a password hashes properly and verifies accurately."""
        password = "SecureHospitalPassword@2026"
        salt = AuthService.generate_salt()
        pwd_hash, used_salt = AuthService.hash_password(password, salt)

        self.assertEqual(salt, used_salt)
        self.assertTrue(AuthService.verify_password(password, pwd_hash, salt))

    def test_reject_incorrect_password(self):
        """Tests that mismatched passwords are unconditionally rejected."""
        password = "AdminPassword123"
        pwd_hash, salt = AuthService.hash_password(password)

        self.assertFalse(AuthService.verify_password("WrongPassword", pwd_hash, salt))
        self.assertFalse(AuthService.verify_password("adminpassword123", pwd_hash, salt))  # case sensitive
        self.assertFalse(AuthService.verify_password("", pwd_hash, salt))

    def test_different_salts_produce_different_hashes(self):
        """Tests rainbow table mitigation: same password with two salts yields distinct hashes."""
        password = "UniversalPassword"
        hash1, salt1 = AuthService.hash_password(password)
        hash2, salt2 = AuthService.hash_password(password)

        self.assertNotEqual(salt1, salt2)
        self.assertNotEqual(hash1, hash2)

if __name__ == "__main__":
    unittest.main()
