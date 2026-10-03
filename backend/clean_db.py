
import sqlite3
conn = sqlite3.connect("scholargraph.db")
c = conn.cursor()
c.execute("DELETE FROM related_papers WHERE source_paper_id=1 AND search_query LIKE \"%diabetic%\"")
conn.commit()
c.execute("SELECT count(*) FROM related_papers WHERE source_paper_id=1")
print(f"Remaining related papers for Paper 1: {c.fetchone()[0]}")
conn.close()

