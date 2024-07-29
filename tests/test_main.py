import unittest
from fastapi.testclient import TestClient
from main import SeurantaApp


class TestSeurantaApp(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(SeurantaApp())


    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


    def test_styles(self):
        response = self.client.get("/static/styles.css")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
