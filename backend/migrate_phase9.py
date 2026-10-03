import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    conn = sqlite3.connect("scholargraph.db")
    cursor = conn.cursor()
    
    try:
        # Drop the old research_gaps table
        cursor.execute("DROP TABLE IF EXISTS research_gaps")
        
        # Create the new table
        cursor.execute("""
            CREATE TABLE research_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                gap_type VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                description TEXT NOT NULL,
                evidence JSON,
                significance TEXT,
                related_paper_ids JSON,
                confidence FLOAT,
                proposed_direction TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(paper_id) REFERENCES papers(id)
            )
        """)
        
        # Create index
        cursor.execute("CREATE INDEX ix_research_gaps_id ON research_gaps (id)")
        
        conn.commit()
        logger.info("Successfully migrated research_gaps table for Phase 9.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
