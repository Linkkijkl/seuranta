import unittest
from fastapi.testclient import TestClient
from src.seuranta_app import SeurantaApp


class TestSeurantaApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testing_options = { "disable_lease_monitor": True,
                                "disable_export": True}


    def setUp(self) -> None:
        with TestClient(app := SeurantaApp(**self.testing_options)) as client: # type: ignore
            self.app = app
            self.client = client


    def test_index_endpoint_exists(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


    def test_static_styles_exists(self):
        response = self.client.get("/static/styles.css")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
