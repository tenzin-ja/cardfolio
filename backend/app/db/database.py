from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# This is the path to our SQLite database file.
# The "./cards.db" part means the database file will be created inside the backend folder.
SQLALCHEMY_DATABASE_URL = "sqlite:///./cards.db"




# The engine is the main connection point between SQLAlchemy and the database.
# connect_args={"check_same_thread": False} is needed for SQLite when using FastAPI.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# SessionLocal creates database sessions.
# A session is like a temporary conversation with the database:
# we can add, read, update, or delete data through it.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Gives each API request its own database session.
"""
Function creates a new session everytime its called
Session opens before each new api request, then closes afterwards.

"""
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# Base is the parent class that our database models inherit from.
# For example, our Card model inherits from Base.
# This lets SQLAlchemy track which tables it needs to create.
Base = declarative_base()