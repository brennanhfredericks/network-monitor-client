import time
import sys
import asyncio
from collections import OrderedDict
from asyncio import Task

from typing import Optional, Dict, Any, Tuple


class Service_Manager(object):
    def __init__(self) -> None:

        # hold a ordered mapping of Task
        self._services: OrderedDict[str, Task] = OrderedDict()

    async def add_service(self, service_name: str, service_obj: Any):
        # add service to Order dict
        task: Task = asyncio.create_task(service_obj)
        self._services[service_name] = task

    async def stop_service(self, service_name):
        # implement later
        raise NotImplemented

    async def stop_all_services(self):

        for k, v in self._services.items():
            # cancel asynchronous task
            v.cancel()
            print(f"Requestd {k} service to stop")
        await asyncio.gather(*self._services.values(), return_exceptions=True)
        print("All services stopped")
        self._services.clear()
