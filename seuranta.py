import sqlite3


class SeurantaDb(sqlite3.Connection):
    def __init__(self, dbfile: str = "seuranta.db") -> None:
        super().__init__(dbfile)
        self._create_tables()


    def _create_tables(self):
        cur = self.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS person (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        );""")
        cur.execute("""CREATE TABLE IF NOT EXISTS device (
            person_id INTEGER PRIMARY KEY REFERENCES person (id),
            macaddress TEXT UNIQUE
        );""")


    @property
    def people(self) -> list[str]:
        cur = self.cursor()
        cur.execute("SELECT name FROM person")
        return list(name for (name,) in cur.fetchall())


    @property
    def tables(self) -> list[str]:
        cur = self.cursor()
        cur.execute("SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%';")
        return list(name for (name,) in cur.fetchall())


    def addpeople(self, people: list[str]):
        cur = self.cursor()
        cur.executemany("INSERT OR IGNORE INTO person VALUES (?, ?)", ((None, person, ) for person in people))
        self.commit()


def main():
    with SeurantaDb() as sdb:
        sdb.addpeople(['45spoons'])
        print(sdb.people)


if __name__ == "__main__":
    main()