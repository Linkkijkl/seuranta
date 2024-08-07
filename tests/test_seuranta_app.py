import unittest
import string
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


    def test_name_form_minor_sanitisation(self):
        form = {"name": "45_spoons"}
        response = self.client.post(
            "/name-form", data=form
        )
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["name"], "45spoons")
        self.assertIsNotNone(data["id"])
        self.assertIsNotNone(data["created_date"])


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
