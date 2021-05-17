import time
import sys
import asyncio
from aiologger import Logger
from collections import OrderedDict
from asyncio import Task, Queue
from enum import Enum

from typing import Optional, Dict, Any, Tuple


class Data_Queue_Identifier(Enum):
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
                             OrderedDict[Service_Identifier, Task]] = {
                                 Service_Type.Producer: OrderedDict(),
                                 Service_Type.Consumer: OrderedDict()}
        self._data_queues: Dict[Data_Queue_Identifier, Queue] = OrderedDict()
        # add formatter

    def add_queue(self, queue: Queue, queue_identifier: Data_Queue_Identifier):
        self._data_queues[queue_identifier] = queue

    def add_service(self, service_type: Service_Type, service_identifier: Service_Identifier, service_obj: Task) -> None:
        # add service to Order dict
        self._services[service_type][service_identifier] = service_obj

    def stop_service(self, service_identifier: Service_Identifier):
        # implement later
        raise NotImplemented

    async def stop_all_services(self) -> None:
        logger = Logger.with_default_handlers(name="service-manager")

        # stop all service that produces data
        for k, v in self._services[Service_Type.Producer].items():
            v.cancel()
            await logger.info(f"Requested {k} service to stop")

        # wait for all queue to be cleared by the consumer services
        for k, v in self._data_queues.items():
            await v.join()
            await logger.info(f"Wait queue {k} to clear")

        # stop all service that consume data
        for k, v in self._services[Service_Type.Consumer].items():
            v.cancel()
            await logger.info(f"Requested {k} service to stop")

        await logger.info("All services stopped")
