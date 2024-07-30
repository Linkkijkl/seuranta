import unittest
from fastapi.testclient import TestClient
from src.seuranta_app import SeurantaApp


class TestSeurantaApp(unittest.TestCase):
    def setUp(self) -> None:
        with TestClient(SeurantaApp(use_lease_monitor=False)) as client:
            self.client = client


    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


    def test_styles(self):
        response = self.client.get("/static/styles.css")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
