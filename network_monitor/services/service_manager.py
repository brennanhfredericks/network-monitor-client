import time
import sys
import asyncio
from aiologger import Logger
from collections import OrderedDict
from asyncio import Task
from enum import Enum

from typing import Optional, Dict, Any, Tuple


class Data_Queue(Enum):
    Raw_Data = 0,
    Processed_Data = 1


class Service_Type(Enum):
    Producer = 0,
    Consumer = 1


class Service_Identifier(Enum):
    Interface_Listener_Service = 0,
    Packet_Parser_Service = 1,
    Packet_Submitter_Service = 2


class Service_Manager(object):
    def __init__(self) -> None:

        # hold a ordered mapping of Task
        self._services: Dict[Service_Type,
                             OrderedDict[Service_Identifier, Task]] = dict(
                                 Service_Type.Producer=OrderedDict(),
                                 Service_Type.Consumer=OrderedDict()
        )
        # add formatter

    def add_queue(self, queue_name: Service_Identifier):
        ...

    def add_service(self, service_type: Service_Type, service_identifier: Service_Identifier, service_obj: Task) -> None:
        # add service to Order dict
        self._services[service_type][service_identifier] = service_obj

    def stop_service(self, service_name):
        # implement later
        raise NotImplemented

    async def stop_all_services(self) -> None:
        logger = Logger.with_default_handlers(name="service-manager")

        # stop listener service first
        self._services[Service_Type.Interface_Listener_Service].cancel()

        for k, v in self._services.items():
            # cancel asynchronous task
            v.cancel()
            await logger.info(f"Requestd {k} service to stop")
            print(f"Requestd {k} service to stop")

        await asyncio.gather(*self._services.values(), return_exceptions=True)
        print("All services stopped")
        await logger.info("All services stopped")
        self._services.clear()
