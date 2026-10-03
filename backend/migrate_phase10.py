import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    conn = sqlite3.connect("scholargraph.db")
    cursor = conn.cursor()
    
    try:
        # Drop if exists
        cursor.execute("DROP TABLE IF EXISTS recent_research")
        
        # Create the new table
        cursor.execute("""
            CREATE TABLE recent_research (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                external_id VARCHAR,
                source VARCHAR,
                title VARCHAR NOT NULL,
                authors JSON,
                abstract TEXT,
                year INTEGER NOT NULL,
                doi VARCHAR,
                url VARCHAR,
                venue VARCHAR,
                citation_count INTEGER,
                relevance_score FLOAT NOT NULL,
                relevance_reason TEXT,
                relationship_type VARCHAR NOT NULL,
                is_newer_than_target BOOLEAN DEFAULT 0,
                addresses_gap BOOLEAN DEFAULT 0,
                related_gap_ids JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(paper_id) REFERENCES papers(id)
            )
        """)
        
        # Create indices
        cursor.execute("CREATE INDEX ix_recent_research_id ON recent_research (id)")
        cursor.execute("CREATE INDEX ix_recent_research_paper_id ON recent_research (paper_id)")
        
        conn.commit()
        logger.info("Successfully migrated recent_research table for Phase 10.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
