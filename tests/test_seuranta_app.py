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


class TestSeurantaAppParsing(unittest.IsolatedAsyncioTestCase):
    async def test_parse_leases_empty(self):
        connected_clients = await SeurantaApp.parse_leases("")
        self.assertListEqual([], connected_clients)


    async def test_parse_leases_one_lease(self):
        connected_clients = await SeurantaApp.parse_leases("0000000000 1a:2b:3c:4d:5e:6f 192.168.1.100 test-hostname 01:1a:2b:3c:4d:5e:6f")
        self.assertListEqual([("1a:2b:3c:4d:5e:6f","192.168.1.100","test-hostname")], connected_clients)


    async def test_parse_leases_two_leases(self):
        lease_str = "0000000000 1a:2b:3c:4d:5e:6f 192.168.1.100 test-hostname-1 01:1a:2b:3c:4d:5e:6f\n1111111111 6f:5e:4d:3c:2b:1a 192.168.1.101 test-hostname-2 01:6f:5e:4d:3c:2b:1a"
        ans = await SeurantaApp.parse_leases(lease_str)
        exp = [("1a:2b:3c:4d:5e:6f","192.168.1.100","test-hostname-1"),
               ("6f:5e:4d:3c:2b:1a","192.168.1.101","test-hostname-2")]
        self.assertListEqual(exp, ans)


if __name__ == "__main__":
    unittest.main(verbosity=2)
