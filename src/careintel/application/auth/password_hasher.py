"""
Password hashing abstraction.
"""

import bcrypt

class PasswordHasher:
    """
    Abstracts password hashing details (bcrypt cost-12).
    """

    def __init__(self) -> None:
        self.rounds = 12

    def hash(self, password: str) -> str:
        """Hash a plaintext password."""
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
        return hashed_bytes.decode('utf-8')

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a hash."""
        pwd_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        try:
            return bcrypt.checkpw(pwd_bytes, hash_bytes)
        except ValueError:
            return False

