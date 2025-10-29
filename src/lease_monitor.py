import aiohttp
import src.utils as utils

class Lease():
    def __init__(self, ipv4_addr: str, hostname: str, mac_addr: str):
        self.ipv4_addr: str = ipv4_addr
        self.hostname: str = hostname
        self.mac_addr: str = mac_addr


    def __eq__(self, other: object) -> bool:
        return self.__dict__ == other.__dict__


class LeaseMonitor():
    _leases: list[Lease] = []
    _req_timeout = aiohttp.ClientTimeout(total=10, connect=5)
    _endpoint = 'http://192.168.1.1/moi'


    @staticmethod
    async def parse_leases(leases_str: str) -> list[Lease]:
        leases: list[Lease] = []
        lease_lines: list[str] = [line for line in leases_str.split("\n") if line]
        for line in lease_lines:
            (_, mac, ip, hostname, _) = line.split()
            leases.append(Lease(ipv4_addr=ip, hostname=hostname, mac_addr=mac))
        return leases


    async def handle_lease_response(self, response: aiohttp.ClientResponse) -> int:
        if response.status >= 400:
            self._leases = []
        else:
            self._leases = await self.parse_leases(await response.text())
        return response.status


    async def fetch_leases(self) -> int:
        async with aiohttp.ClientSession(timeout=self._req_timeout) as session:
            async with session.get(self._endpoint) as response:
                return await self.handle_lease_response(response)


    async def update_leases(self) -> int:
        status = await self.fetch_leases()
        await utils.export_names("balls")
        return status


    async def get_lease_by_ip(self, ipv4_addr: str | None) -> Lease | None:
        for lease in self.leases:
            if lease.ipv4_addr == ipv4_addr:
                return lease
        return None


    @property
    def leases(self) -> list[Lease]:
        return self._leases.copy()

    @property
    def mac_addrs(self) -> list[str]:
        return [lease.mac_addr for lease in self.leases]
