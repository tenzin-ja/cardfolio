import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import ConfigurationError, get_jwt_secret_key
from app.db.database import get_db
from app.models.user import User
from app.security import JWT_ALGORITHM


# Extract the bearer token; handle missing credentials ourselves for a clear 401.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate the access token and retrieve its user."""

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            get_jwt_secret_key(),
            # Only accept our chosen algorithm, not whatever the token requests.
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat"]},
        )

        user_id = int(payload["sub"])

        # Match the positive PostgreSQL Integer IDs used by the users table.
        if not 1 <= user_id <= 2_147_483_647:
            raise ValueError("Invalid user ID.")

    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured.",
        ) from exc
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise unauthorized from exc

    # A valid signature isn't enough if the account no longer exists.
    user = db.get(User, user_id)

    if user is None:
        raise unauthorized

    return user