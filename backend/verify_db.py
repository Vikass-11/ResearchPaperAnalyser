import sqlite3
conn = sqlite3.connect('scholargraph.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in c.fetchall()]
for table in tables:
    if table != 'sqlite_sequence':
        c.execute(f'SELECT COUNT(*) FROM "{table}"')
        print(f'{table}: {c.fetchone()[0]}')
