import unittest
from fastapi.testclient import TestClient
from src.seuranta_app import SeurantaApp, Lease


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


class TestLease(unittest.TestCase):
    def test_lease_are_not_equal(self):
        lease_a = Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f")
        lease_b = Lease("192.168.1.101","test-hostname-2","6f:5e:4d:3c:2b:1a")
        self.assertNotEqual(lease_a, lease_b)


    def test_lease_are_equal(self):
        lease_a = Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f")
        lease_b = Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f")
        self.assertEqual(lease_a, lease_b)


class TestSeurantaAppLeaseParsing(unittest.IsolatedAsyncioTestCase):
    async def test_parse_leases_zero_leases(self):
        connected_clients = await SeurantaApp.parse_leases("")
        self.assertListEqual([], connected_clients)


    async def test_parse_leases_one_lease(self):
        active_leases = await SeurantaApp.parse_leases("0000000000 1a:2b:3c:4d:5e:6f 192.168.1.100 test-hostname 01:1a:2b:3c:4d:5e:6f")
        self.assertEqual(1, len(active_leases))
        active_lease = active_leases.pop()
        expected_lease = Lease("192.168.1.100", "test-hostname", "1a:2b:3c:4d:5e:6f")
        self.assertEqual(active_lease, expected_lease)


    async def test_parse_leases_two_leases(self):
        lease_lines = ["0000000000 1a:2b:3c:4d:5e:6f 192.168.1.100 test-hostname-1 01:1a:2b:3c:4d:5e:6f",
                       "1111111111 6f:5e:4d:3c:2b:1a 192.168.1.101 test-hostname-2 01:6f:5e:4d:3c:2b:1a"]
        active_leases = await SeurantaApp.parse_leases("\n".join(lease_lines))
        self.assertEqual(2, len(active_leases))
        expected_lease = [Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f"),
                          Lease("192.168.1.101","test-hostname-2","6f:5e:4d:3c:2b:1a")]
        for ans, exp in zip(active_leases, expected_lease):
            self.assertEqual(ans, exp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
