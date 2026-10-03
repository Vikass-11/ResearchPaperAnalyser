import sqlite3

def upgrade():
    conn = sqlite3.connect('scholargraph.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE related_papers ADD COLUMN relationship_type VARCHAR;")
    except sqlite3.OperationalError as e:
        print(f"Skipping relationship_type: {e}")
        
    try:
        cursor.execute("ALTER TABLE related_papers ADD COLUMN score_breakdown JSON;")
    except sqlite3.OperationalError as e:
        print(f"Skipping score_breakdown: {e}")
        
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    upgrade()
