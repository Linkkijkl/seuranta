import unittest
from unittest.mock import PropertyMock, patch
import string
from fastapi.testclient import TestClient
from src.seuranta_app import SeurantaApp, get_session
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from src.lease_monitor import Lease
from src.db import *


class TestSeurantaApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testing_options = {  }


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


    def test_index_endpoint_exists(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


    def test_static_styles_exists(self):
        response = self.client.get("/static/styles.css")
        self.assertEqual(response.status_code, 200)


    def test_name_form_minor_sanitisation(self):
        with patch("src.seuranta_app.SeurantaApp.leases", new_callable=PropertyMock) as mock_leases:
            mock_leases.return_value = self.leases
            form = {"name": "45_spoons"}
            self.client.post("/name-form",  data=form)

            result = self.dbsession.get_one(TrackedEntity, 1)

            self.assertEqual(result.name, "45spoons")


    def test_name_form_links_device(self):
        with patch("src.seuranta_app.SeurantaApp.leases", new_callable=PropertyMock) as mock_leases:
            mock_leases.return_value = self.leases
            form = {"name": "45spoons"}
            self.client.post("/name-form",  data=form)

            entity = self.dbsession.get_one(TrackedEntity, 1)
            device = self.dbsession.get_one(Device, 1)

            self.assertEqual(device.trackedentity_id, entity.id)


    def test_name_form_creates_device(self):
        with patch("src.seuranta_app.SeurantaApp.leases", new_callable=PropertyMock) as mock_leases:
            mock_leases.return_value = self.leases
            form = {"name": "45spoons"}
            self.client.post("/name-form",  data=form)

            device = self.dbsession.get_one(Device, 1)

            self.assertEqual(device.mac, "1a:2b:3c:4d:5e:6f")


class TestNameSanitisation(unittest.IsolatedAsyncioTestCase):
    async def test_trim_leading_whitespace(self):
        result = await SeurantaApp.sanitise_name(" alex")
        self.assertEqual(result, "alex")


    async def test_trim_trailing_whitespace(self):
        result = await SeurantaApp.sanitise_name("alex ")
        self.assertEqual(result, "alex")


    async def test_remove_bounded_whitespace(self):
        result = await SeurantaApp.sanitise_name("al ex")
        self.assertEqual(result, "alex")


    async def test_cut_long_name(self):
        result = await SeurantaApp.sanitise_name("XXXXXEEEEEXXXXXEEEEEz")
        self.assertEqual(result, "XXXXXEEEEEXXXXXEEEEE")


    async def test_valid_name(self):
        result = await SeurantaApp.sanitise_name("AlexIs45spoons")
        self.assertEqual(result, "AlexIs45spoons")


    async def test_remove_punctuation_characters(self):
        for char in string.punctuation:
            with self.subTest(char=char):
                result = await SeurantaApp.sanitise_name(f"al{char}ex")
                self.assertEqual(result, "alex")


if __name__ == "__main__":
    unittest.main(verbosity=2)
