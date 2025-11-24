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

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(engine)


with sqlite3.connect("seuranta.db") as con:

    with SessionLocal() as session:
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
            tracked_entity = models.TrackedEntity(id=item[1], name=item[0], created_datetime=datetime.datetime.fromisoformat(item[2]))
            tracked_entities[item[1]] = tracked_entity

        res = cur.execute("SELECT * FROM device")
        while item := res.fetchone():
            device = models.Device(id=item[3], mac_addr=item[1], hostname=item[0], tracked_entity_id=item[2])
            tracked_entities[device.tracked_entity_id].devices.append(device)

        remove = []
        for (id, te) in tracked_entities.items():
            if not len(te.devices):
                remove.append(id)

        for id in remove:
            tracked_entities.pop(id)

        for te in tracked_entities.values():
            print(te)
        session.add_all(tracked_entities.values())
        session.commit()
