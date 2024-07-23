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
            mac_address TEXT UNIQUE
        );""")


    @property
    def devices(self) -> list[str]:
        cur = self.cursor()
        cur.execute("SELECT mac_address FROM device")
        return list(mac_address for (mac_address,) in cur.fetchall())


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


    def name_to_person_id(self, name: str) -> int:
        cur = self.cursor()
        cur.execute("SELECT id FROM person WHERE name = ?", (name,))
        (id,) = cur.fetchone()
        return id


    def add_people(self, people: list[str]):
        cur = self.cursor()
        cur.executemany("INSERT OR IGNORE INTO person VALUES (?, ?)", ((None, person, ) for person in people))
        self.commit()


def main():
    with SeurantaDb() as sdb:
        sdb.add_people(['45spoons'])
        print(sdb.people)


if __name__ == "__main__":
    main()