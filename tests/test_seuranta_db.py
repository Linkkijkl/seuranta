import unittest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from src.db import *

from src.seuranta_app import SeurantaApp, get_session


class TestSeurantaDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testing_options = {"disable_export": True}


    def setUp(self) -> None:
        self.leases = [Lease("testclient","test-hostname-1","1a:2b:3c:4d:5e:6f"),
                        Lease("192.168.1.101","test-hostname-2","6f:5e:4d:3c:2b:1a")]
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            self.dbsession = session
            def get_session_override():
                return session
            with TestClient(app := SeurantaApp(**self.testing_options)) as client: # type: ignore
                self.app = app
                self.client = client
                app.dependency_overrides[get_session] = get_session_override


    def test_name_form(self):
        form = {"name": "Alex"}
        self.client.post("/name-form", data=form)

        result = self.dbsession.get_one(TrackedEntity, 1)

        self.assertEqual(result.name, "Alex")


if __name__ == "__main__":
    unittest.main(verbosity=2)
