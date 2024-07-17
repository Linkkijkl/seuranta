import sqlite3


def main():
    with sqlite3.connect('seuranta.db') as conn:
        cur = conn.cursor()
    
        cur.execute("""CREATE TABLE IF NOT EXISTS person (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )""")
    
        cur.execute("INSERT OR IGNORE INTO person VALUES (?, ?)", (None, "45spoons"))
        conn.commit()


if __name__ == "__main__":
    main()