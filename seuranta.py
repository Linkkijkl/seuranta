import sqlite3

with sqlite3.connect('seuranta.db') as conn:
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS person (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )""")