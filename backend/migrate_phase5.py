import os
from sqlalchemy import create_engine, text
from app.models.schema import Base

DB_PATH = os.path.join(os.path.dirname(__file__), "app", "scholargraph.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

def migrate():
    print(f"Connecting to database at {DB_PATH}")
    # Fallback to local db if not in app/
    if not os.path.exists(DB_PATH):
        alt_db = os.path.join(os.path.dirname(__file__), "scholargraph.db")
        print(f"Trying alternative path: {alt_db}")
        engine = create_engine(f"sqlite:///{alt_db}")
    else:
        engine = create_engine(DATABASE_URL)
    
    # Alter tables manually since create_all doesn't alter existing tables in SQLite
    # We will use raw SQL for SQLite
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE related_papers ADD COLUMN is_existing_reference BOOLEAN DEFAULT 0;"))
        except Exception as e:
            print(f"is_existing_reference column likely already exists: {e}")
            
        try:
            conn.execute(text("ALTER TABLE related_papers ADD COLUMN search_query VARCHAR;"))
        except Exception as e:
            print(f"search_query column likely already exists: {e}")
            
        try:
            conn.execute(text("ALTER TABLE related_papers ADD COLUMN discovery_source VARCHAR;"))
        except Exception as e:
            print(f"discovery_source column likely already exists: {e}")

        try:
            conn.execute(text("ALTER TABLE related_papers ADD COLUMN paper_type VARCHAR;"))
        except Exception as e:
            print(f"paper_type column likely already exists: {e}")

        try:
            conn.execute(text("ALTER TABLE related_papers ADD COLUMN keywords JSON;"))
        except Exception as e:
            print(f"keywords column likely already exists: {e}")
            
        try:
            conn.execute(text("ALTER TABLE research_profiles ADD COLUMN key_concepts JSON;"))
        except Exception as e:
            print(f"key_concepts column likely already exists: {e}")
            
        try:
            conn.execute(text("ALTER TABLE research_profiles ADD COLUMN application_domain VARCHAR;"))
        except Exception as e:
            print(f"application_domain column likely already exists: {e}")

    print("Phase 5 Migration complete!")

if __name__ == "__main__":
    migrate()
