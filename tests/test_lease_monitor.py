import unittest
from unittest.mock import AsyncMock, PropertyMock, patch
from src.lease_monitor import Lease, LeaseMonitor


class TestLease(unittest.TestCase):
    def test_lease_are_not_equal(self):
        lease_a = Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f")
        lease_b = Lease("192.168.1.101","test-hostname-2","6f:5e:4d:3c:2b:1a")
        self.assertNotEqual(lease_a, lease_b)


    def test_lease_are_equal(self):
        lease_a = Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f")
        lease_b = Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f")
        self.assertEqual(lease_a, lease_b)


class TestLeaseMonitorLeaseParsing(unittest.IsolatedAsyncioTestCase):
    async def test_parse_leases_zero_leases(self):
        connected_clients = await LeaseMonitor.parse_leases("")
        self.assertListEqual([], connected_clients)


    async def test_parse_leases_one_lease(self):
        active_leases = await LeaseMonitor.parse_leases("0000000000 1a:2b:3c:4d:5e:6f 192.168.1.100 test-hostname 01:1a:2b:3c:4d:5e:6f")
        self.assertEqual(1, len(active_leases))
        active_lease = active_leases.pop()
        expected_lease = Lease("192.168.1.100", "test-hostname", "1a:2b:3c:4d:5e:6f")
        self.assertEqual(active_lease, expected_lease)


    async def test_parse_leases_two_leases(self):
        lease_lines = ["0000000000 1a:2b:3c:4d:5e:6f 192.168.1.100 test-hostname-1 01:1a:2b:3c:4d:5e:6f",
                       "1111111111 6f:5e:4d:3c:2b:1a 192.168.1.101 test-hostname-2 01:6f:5e:4d:3c:2b:1a"]
        active_leases = await LeaseMonitor.parse_leases("\n".join(lease_lines))
        self.assertEqual(2, len(active_leases))
        expected_lease = [Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f"),
                          Lease("192.168.1.101","test-hostname-2","6f:5e:4d:3c:2b:1a")]
        for ans, exp in zip(active_leases, expected_lease):
            self.assertEqual(ans, exp)


class TestLeaseMonitor(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_on_update = AsyncMock()


    async def test_lease_monitor_calls_on_update(self):
        with patch.object(LeaseMonitor, "fetch_leases", return_value = 200):
            lease_monitor = LeaseMonitor("", self.mock_on_update)
            await lease_monitor.update_leases()
            self.mock_on_update.assert_called()


    async def test_get_lease_by_id_exists(self):
        with patch.object(LeaseMonitor, "leases", new_callable=PropertyMock) as mock_leases:
            leases = [Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f"),
                    Lease("192.168.1.101","test-hostname-2","6f:5e:4d:3c:2b:1a")]
            mock_leases.return_value = leases
            lease_monitor = LeaseMonitor("", self.mock_on_update)
            result_lease = await lease_monitor.get_lease_by_ip("192.168.1.100")
            expected_lease = Lease("192.168.1.100", "test-hostname-1", "1a:2b:3c:4d:5e:6f")
            self.assertEqual(result_lease, expected_lease)


    async def test_get_lease_by_id_ip_not_leased_returns_none(self):
        with patch("src.lease_monitor.LeaseMonitor.leases", new_callable=PropertyMock) as mock_leases:
            leases = []
            mock_leases.return_value = leases
            lease_monitor = LeaseMonitor("", self.mock_on_update)
            result_lease = await lease_monitor.get_lease_by_ip("192.168.1.100")
            self.assertIsNone(result_lease)


if __name__ == "__main__":
    unittest.main(verbosity=2)
