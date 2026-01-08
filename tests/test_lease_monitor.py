import pytest, pytest_asyncio
import unittest
from unittest.mock import AsyncMock, PropertyMock, patch
from src.lease_monitor import Lease, LeaseMonitor
import src.utils as utils


@pytest_asyncio.fixture
async def mock_leasemonitor(monkeypatch, mock_leases):
    monkeypatch.setattr(LeaseMonitor, "leases", mock_leases)
    monkeypatch.delattr(utils, "export_names")
    leasemonitor = LeaseMonitor()
    return leasemonitor

def test_lease_are_not_equal():
    lease_a = Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f")
    lease_b = Lease("192.168.1.101","test-hostname-2","6f:5e:4d:3c:2b:1a")
    assert lease_a != lease_b

def test_lease_are_equal():
    lease_a = Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f")
    lease_b = Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f")
    assert lease_a == lease_b

@pytest.mark.asyncio
async def test_parse_leases_zero_leases():
    connected_clients = await LeaseMonitor.parse_leases("")
    assert [] == connected_clients

@pytest.mark.asyncio
async def test_parse_leases_one_lease():
    active_leases = await LeaseMonitor.parse_leases("0000000000 1a:2b:3c:4d:5e:6f 192.168.1.100 test-hostname 01:1a:2b:3c:4d:5e:6f")
    assert len(active_leases) == 1
    active_lease = active_leases.pop()
    expected_lease = Lease("192.168.1.100", "test-hostname", "1a:2b:3c:4d:5e:6f")
    assert active_lease == expected_lease

@pytest.mark.asyncio
async def test_parse_leases_two_leases(mock_leases):
    lease_lines = ["0000000000 1a:2b:3c:4d:5e:6f 192.168.1.100 test-hostname-1 01:1a:2b:3c:4d:5e:6f",
                    "1111111111 6f:5e:4d:3c:2b:1a 192.168.1.101 test-hostname-2 01:6f:5e:4d:3c:2b:1a"]
    active_leases = await LeaseMonitor.parse_leases("\n".join(lease_lines))
    assert len(active_leases) == 2
    expected_leases = [Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f"),
                        Lease("192.168.1.101","test-hostname-2","6f:5e:4d:3c:2b:1a")]
    for ans, exp in zip(active_leases, expected_leases):
        assert ans == exp

@pytest.mark.asyncio
async def test_get_lease_by_id_exists(mock_leasemonitor):
    result_lease = await mock_leasemonitor.get_lease_by_ip("192.168.1.100")
    expected_lease = Lease("192.168.1.100", "test-hostname-1", "1a:2b:3c:4d:5e:6f")
    assert result_lease == expected_lease

@pytest.mark.asyncio
async def test_get_lease_by_id_ip_not_leased_returns_none(mock_leasemonitor):
    result_lease = await mock_leasemonitor.get_lease_by_ip("192.168.1.102")
    assert result_lease is None
