from fastapi import APIRouter, Depends, HTTPException, status
from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.config import ConfigurationError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    registration: UserRegister,
    db: Session = Depends(get_db),
):
    """Create an account and return its details without the password hash"""

    # Hash the password before putting it into the user record
    user = User(
        email=registration.email,
        password_hash=hash_password(registration.password),
    )

    # Prepare the new record, then save it to the database
    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        # Undo the failed transaction so the session can be used again
        db.rollback()

        # Check that the failure came from an email already being registered
        # Other database errors should not be treated as duplicate accounts
        if (
            isinstance(exc.orig, UniqueViolation)
            and exc.orig.diag.constraint_name == "uq_users_email"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from exc

        # Let unrelated errors continue through the normal error handling
        raise

    # Load values the database generated, such as the ID and creation time
    db.refresh(user)

    # FastAPI uses UserResponse to keep the password hash out of the response
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """Verify credentials and issue a short-lived access token."""

    user = (
        db.query(User)
        .filter(User.email == credentials.email)
        .first()
    )

    stored_hash = (
        user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    )
    password_is_valid = verify_password(credentials.password, stored_hash)

    # Don't reveal whether the email or password was incorrect.
    if user is None or not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        access_token = create_access_token(user.id)
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured.",
        ) from exc

    return TokenResponse(access_token=access_token)