from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import get_jwt_secret_key


JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hasher = PasswordHash.recommended()

# Check a hash even when the email isn't registered, so that failure path
# doesn't skip the expensive password check and return noticeably faster
DUMMY_PASSWORD_HASH = password_hasher.hash("unused-dummy-password")

def hash_password(password: str) -> str:
    """Hash a password before it reaches database storage."""
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a submitted password against the saved hash."""
    return password_hasher.verify(password, stored_hash)


def create_access_token(user_id: int) -> str:
    """Create a signed token identifying the user for a limited time."""

    now = datetime.now(timezone.utc)

    #info backend passes to jwt. 
    payload = {
        # JWT subjects are strings. Use the stable user ID, not their email.

        #subject: who the token belongs to, for ex user id: 5 = sub: 5
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    #Create the auth token, jwt key is used to calcuate a unique signature to prevent unauth modifications
    return jwt.encode(
        payload,
        get_jwt_secret_key(),
        algorithm=JWT_ALGORITHM,
    )