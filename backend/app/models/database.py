import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from .schema import Base

# Determine database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scholargraph.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False, "timeout": 15} if DATABASE_URL.startswith("sqlite") else {}
)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
