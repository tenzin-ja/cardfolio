import os
from pathlib import Path
import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

#registers the function to run whenever any SQLAlchemy engine opens a connection.
@event.listens_for(Engine, "connect")
def enable_sqliteforeign_keys(dbapi_connection, _connection_record):
    #ensures the SQLite-only command is not sent to PostgreSQL
    if isinstance(dbapi_connection, sqlite3,Connection):
        cursor = dbapi_connection,cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()



# Build the default path from this source file so starting Python from a
# different working directory cannot accidentally create another database.
BACKEND_DIR = Path(__file__).resolve().parents[2]
#Finds the database
DEFAULT_DATABASE_PATH = BACKEND_DIR / "cards.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"

# Tests and deployed environments can provide their own database without
# changing application code.
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    DEFAULT_DATABASE_URL,
)

# SQLite needs this option for FastAPI requests that may use different threads.
# Other databases, such as PostgreSQL, do not accept this SQLite-only setting.
connect_args = (
    {"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {}
)


#Creates engine to manage connections 
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
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

# Acts as a marker on models for database table
Base = declarative_base()