
import sqlite3
conn = sqlite3.connect("scholargraph.db")
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS literature_surveys")
conn.commit()
conn.close()

from app.models.database import engine
from app.models.schema import Base
print("Creating new literature_surveys table...")
Base.metadata.create_all(bind=engine)
print("Done.")

