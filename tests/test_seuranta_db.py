import unittest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.seuranta_app import SeurantaApp, get_session


class TestSeurantaDb(unittest.TestCase):
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

            testing_options = { "disable_lease_monitor": True,
                                "disable_export": True}
            with TestClient(app := SeurantaApp(**testing_options)) as client: # type: ignore
                self.testclient = client
                app.dependency_overrides[get_session] = get_session_override
                self.app = app # needed for teardown, TODO maybe fixtures would avoid this


    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()


    def test_create_trackedentity_empty_json(self):
        response = self.testclient.post(
            "/tracked", json={}
        )

        self.assertEqual(response.status_code, 422)


    def test_create_trackedentity_valid_json(self):
        response = self.testclient.post(
            "/tracked", json={"name": "Alex"}
        )
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["name"], "Alex")
        self.assertIsNotNone(data["id"])
        self.assertIsNotNone(data["created_date"])


    def test_name_form(self):
        form = {"name": "Alex"}
        response = self.testclient.post(
            "/name-form", data=form
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
