from typing import Any, Optional, Callable, Coroutine
import logging
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler # type: ignore
from apscheduler.triggers.cron import CronTrigger # type: ignore


class Lease():
    def __init__(self, ipv4_addr: str, hostname: str, mac_addr: str):
        self.ipv4_addr: str = ipv4_addr
        self.hostname: str = hostname
        self.mac_addr: str = mac_addr


    def __eq__(self, other: object) -> bool:
        return self.__dict__ == other.__dict__


class LeaseMonitor(AsyncIOScheduler):
    _leases: list[Lease] = []
    _req_timeout = aiohttp.ClientTimeout(total=10, connect=5)
    def __init__(self, endpoint: str, \
            on_update: Optional[Callable[..., Coroutine[Any, Any, Any]]], \
            **kwargs: dict[str, Any] \
        ) -> None:
        super().__init__() # type: ignore
        self.__dict__.update(kwargs)
        self.on_update = on_update
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.WARNING)
        logging.getLogger('apscheduler').setLevel(self._logger.level)
        self._endpoint = endpoint
        self.add_job(self.update_leases, CronTrigger(second="*/15")) # type: ignore
        self.start()
        return


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


    async def update_leases(self) -> int:
        async with aiohttp.ClientSession(timeout=self._req_timeout) as session:
            async with session.get(self._endpoint) as response:
                status = await self.handle_lease_response(response)
        if self.on_update:
            await self.on_update()
        return status


    @property
    def leases(self) -> list[Lease]:
        return self._leases.copy()
