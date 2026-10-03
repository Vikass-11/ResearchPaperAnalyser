import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "scholargraph.db")

def migrate():
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE papers ADD COLUMN web_impact_analysis TEXT;")
        conn.commit()
        print("Successfully added web_impact_analysis column to papers table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column web_impact_analysis already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
