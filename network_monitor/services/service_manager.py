import time
import sys
import asyncio
from collections import OrderedDict
from asyncio import Task
from aiologger import Logger

from typing import Optional, Dict, Any, Tuple


class Service_Manager(object):
    def __init__(self) -> None:

        # hold a ordered mapping of Task
        self._services: OrderedDict[str, Task] = OrderedDict()
        # add formatter
        self.logger = Logger.with_default_handlers(name="service-manager")

    def add_service(self, service_name: str, service_obj: Task) -> None:
        # add service to Order dict
        self._services[service_name] = service_obj

    def stop_service(self, service_name):
        # implement later
        raise NotImplemented

    async def stop_all_services(self) -> None:

        for k, v in self._services.items():
            # cancel asynchronous task
            v.cancel()
            await self.logger.info(f"Requestd {k} service to stop")
            print(f"Requestd {k} service to stop")
        await asyncio.gather(*self._services.values(), return_exceptions=True)
        print("All services stopped")
        await self.logger.info("All services stopped")
        self._services.clear()
