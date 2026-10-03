import os
from sqlalchemy import create_engine
from app.models.schema import Base

DB_PATH = os.path.join(os.path.dirname(__file__), "scholargraph.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

def migrate():
    print(f"Connecting to database at {DB_PATH}")
    engine = create_engine(DATABASE_URL)
    
    # create_all will only create tables that do not already exist
    print("Creating missing tables...")
    Base.metadata.create_all(bind=engine)
    print("Migration complete! Literature survey tables added safely.")

if __name__ == "__main__":
    migrate()
