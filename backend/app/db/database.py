from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_database_url

SQLALCHEMY_DATABASE_URL = get_database_url()

#Allows sqlalchemy to connect to the database, translates sqlalchemy to sql to database
engine = create_engine(SQLALCHEMY_DATABASE_URL)

#Workspace for making changes to the database, bind connects session to engine
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

def get_db():
    #Sessionlocal() starts the session
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base = declarative_base()