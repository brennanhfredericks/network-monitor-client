
import sys
import asyncio

import threading

from logging import Formatter
from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler
from collections import OrderedDict
from dataclasses import dataclass

from enum import Enum

from typing import Optional, Dict, Any, Tuple, Union


@dataclass
class Service_Control(object):
    name: str
    thread: Optional[threading.Thread] = None
    sentinal: bool = True
    loop: Optional[asyncio.AbstractEventLoop] = None

    in_queue: Optional[asyncio.Queue] = None
    out_queue: Optional[asyncio.Queue] = None
    error: Optional[bool] = None


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

        self._data_queues: Dict[Data_Queue_Identifier,
                                asyncio.Queue] = OrderedDict()

        self._services: OrderedDict[Service_Identifier,
                                    Service_Control] = OrderedDict()

        self.terminate: Optional[bool] = None
        self._logger = Logger().with_default_handlers()

        # stream_format = Formatter(
        #     "%(asctime)s"
        # )

        # # configure asynchronous stream logger
        # stream_handler = AsyncStreamHandler(
        #     stream=sys.stdout, formatter=stream_format)
        # self._logger.add_handler(stream_handler)

    async def data_queue_status(self):
        for k, v in self._data_queues.items():
            await self._logger.info(f"{k} size: {v.qsize()}")

    async def performance(self):
        ...

    def check_for_exceptions(self) -> bool:
        for k, v in self._services.items():
            print(k, v.error)
        return any(list(v.error for v in self._services.values()))

    def register_queue_reference(self, queue_identifier: Data_Queue_Identifier, data_queue: asyncio.Queue) -> None:
        """
            Add a new data queue that used to share data between threads
        """
        self._data_queues[queue_identifier] = data_queue

    def retrieve_queue_reference(self, queue_identifier: Data_Queue_Identifier) -> asyncio.Queue:
        """
            Get a reference to a data queue in order to configure endpoint
        """
        return self._data_queues[queue_identifier]

    def add_service(self, service_identifier: Service_Identifier, service_control: Service_Control) -> None:
        # use service manager to handle threads
        self._services[service_identifier] = service_control

        # start thread
        self._services[service_identifier].thread.start()

    def stop_service(self, service_identifier: Service_Identifier):
        print(f"requested: {service_identifier} to stop")
        service_control = self._services.pop(service_identifier)
        service_control.sentinal = False
        if service_control.loop is not None:
            print(asyncio.all_tasks(service_control.loop))

        service_control.thread.join()
        print(f"terminated: {service_identifier} has been closed")

    def stop_all_service(self) -> None:
        service_keys = list(self._services.keys())
        for service_key in service_keys:
            self.stop_service(service_key)

    async def close_application(self) -> None:

        # stop listener service

        self.stop_service(
            Service_Identifier.Interface_Listener_Service)

        # wait for packet service to clear the raw data queue
        self.retrieve_queue_reference(Data_Queue_Identifier.Raw_Data).join()

        # # stop packet parser service
        # self.stop_service(Service_Identifier.Packet_Parser_Service)

        # # wait for packet submiiter to clear the raw data queue
        # self.retrieve_queue_reference(
        #     Data_Queue_Identifier.Processed_Data).join()

        # # stop packet submitter service
        # self.stop_service(Service_Identifier.Packet_Submitter_Service)

        await self._logger.info("all services have been stopped")
