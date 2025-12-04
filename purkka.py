import sqlite3
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import src.models as models
import datetime


PG_USERNAME = ""
PG_DBNAME = ""
PG_PASSWD = ""
DB_HOST = ""
DB_URL = f"postgresql://{PG_USERNAME}:{PG_PASSWD}@{DB_HOST}/{PG_DBNAME}"
OLD_DB = "seuranta.db"

engine = create_engine(DB_URL)
models.Base.metadata.create_all(engine)
SessionLocal = sessionmaker(engine)

def migrate():
    with sqlite3.connect(OLD_DB) as con, SessionLocal() as session:
        pgdevices = session.scalars(select(models.Device)).all()
        for device in pgdevices:
            print(device.mac_addr)

        pgtrackeds = session.scalars(select(models.TrackedEntity)).all()
        for te in pgtrackeds:
            print(te.name)

        cur = con.cursor()

        res = cur.execute("SELECT * FROM trackedentity")
        tracked_entities = {}
        while item := res.fetchone():
            tracked_entities[item[1]] = models.TrackedEntity(name=item[0], created_datetime=datetime.datetime.fromisoformat(item[2]))

        res = cur.execute("SELECT * FROM device")
        while item := res.fetchone():
            tracked_entities[item[2]].devices.append(models.Device(mac_addr=item[1], hostname=item[0]))

        remove = []
        for (id, te) in tracked_entities.items():
            if not len(te.devices):
                remove.append(id)

        for id in remove:
            tracked_entities.pop(id)

        for te in tracked_entities.values():
            print(te)
            session.add(te)

        session.commit()

def inspect():
    with SessionLocal() as session:
        pgtrackeds = session.scalars(select(models.TrackedEntity)).all()
        for te in pgtrackeds:
            print(te)

migrate()
inspect()
