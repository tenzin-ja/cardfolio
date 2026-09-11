from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func

from app.db.database import Base


class User(Base):
    """An account that can sign in and own collection items."""

    __tablename__ = "users"

    __table_args__ = (
        # The database also enforces uniqueness if two registrations arrive together.
        UniqueConstraint("email", name="uq_users_email"),
    )

    id = Column(Integer, primary_key=True)

    # Registration will normalize emails before saving them.
    email = Column(String(320), nullable=False)

    # Store only the password hash, never the original password.
    password_hash = Column(String(255), nullable=False)

    # PostgreSQL supplies the timestamp when the account is created.
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )