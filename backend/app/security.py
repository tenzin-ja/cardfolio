from pwdlib import PasswordHash


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password before it reaches database storage"""
    return password_hasher.hash(password)