import unittest
from fastapi.testclient import TestClient
from src.seuranta_app import SeurantaApp, get_session
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


class TestSeurantaApp(unittest.TestCase):
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


    def test_index_endpoint_exists(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


    def test_static_styles_exists(self):
        response = self.client.get("/static/styles.css")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
