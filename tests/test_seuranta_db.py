import unittest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.seuranta_app import SeurantaApp, get_session


class TestSeurantaDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testing_options = { "disable_lease_monitor": True,
                                "disable_export": True}


    def setUp(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            def get_session_override():
                return session
            with TestClient(app := SeurantaApp(**self.testing_options)) as client: # type: ignore
                self.app = app
                self.client = client
                app.dependency_overrides[get_session] = get_session_override


    @unittest.skip("no longer getting a direct response")
    def test_name_form(self):
        form = {"name": "Alex"}
        response = self.client.post(
            "/name-form", data=form
        )
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["name"], "Alex")
        self.assertIsNotNone(data["id"])
        self.assertIsNotNone(data["created_date"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
