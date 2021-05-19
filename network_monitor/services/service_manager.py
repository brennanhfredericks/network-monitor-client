import time
import sys
import asyncio
import threading

from aiologger import Logger
from collections import OrderedDict
from dataclasses import dataclass

from enum import Enum

from typing import Optional, Dict, Any, Tuple, Union


@dataclass
class Thread_Control(object):

    handler: Optional[threading.Thread] = None
    sentinal: bool = True
    loop: Optional[asyncio.AbstractEventLoop] = None
    error_state: Optional[bool] = None


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
                             OrderedDict[Service_Identifier, Union[asyncio.Task, threading.Thread]]] = {
                                 Service_Type.Producer: OrderedDict(),
                                 Service_Type.Consumer: OrderedDict()}
        self._data_queues: Dict[Data_Queue_Identifier,
                                asyncio.Queue] = OrderedDict()

        self._threads: OrderedDict[str, Thread_Control] = OrderedDict()

        self.logger = Logger.with_default_handlers(name="service-manager")
        # add formatter

    async def status(self):
        for k, v in self._data_queues.items():
            await self.logger.info(f"Queue: {k} Size: {v.qsize()}")

    def add_queue(self, queue: asyncio.Queue, queue_identifier: Data_Queue_Identifier) -> None:
        """
            Add a new data queue that used to share data between asynchronous tasks and/or threads 
        """
        self._data_queues[queue_identifier] = queue

    def get_queue(self, queue_identifier: Data_Queue_Identifier) -> asyncio.Queue:
        """
            Get a reference to a data queue in order to configure endpoint
        """
        return self._data_queues[queue_identifier]

    def add_thread(self, thread_name: str, thread_control: Thread_Control) -> None:
        # use service manager to handle threads
        self._threads[thread_name] = thread_control

        # start thread
        self._threads[thread_name].handler.start()

    def stop_thread(self, thread_name: str):

        self._threads[thread_name].sentinal = False
        print(f"joining thread {thread_name}")
        print(self._threads[thread_name].handler.is_alive(),
              self._threads[thread_name].handler.ident)
        self._threads[thread_name].handler.join()

        # remove thread reference
        self._threads.pop(thread_name)
        print(f"thread {thread_name} has been stopped")

    def stop_threads(self):

        for t_name, t_ctrl in self._threads.items():
            print(f"stopping thread {t_name}")
            # stop while loop for running
            t_ctrl.sentinal = False
            # wait for thread to join
            t_ctrl.handler.join()
            print(f"thread {t_name} has been stopped")

    def add_service(self, service_type: Service_Type, service_identifier: Service_Identifier, service_asyncio_task: asyncio.Task) -> None:
        # add service to Order dict
        self._services[service_type][service_identifier] = service_asyncio_task

    def stop_service(self, service_identifier: Service_Identifier):
        # implement later
        raise NotImplemented

    async def stop_all_services(self) -> None:

        # stop all service that produces data
        for k, v in self._services[Service_Type.Producer].items():
            await self.logger.info(f"Requesting producer {k} service to stop")
            v.cancel()

        # wait for all queue to be cleared by the consumer services
        for k, v in self._data_queues.items():
            await self.logger.info(f"Waiting for queue {k} to clear")
            await v.join()

        # stop all service that consume data
        for k, v in self._services[Service_Type.Consumer].items():
            await self.logger.info(f"Requesting consumer {k} service to stop")
            v.cancel()

        # join threads
        for k in self._threads:
            for t_k, v in self._threads[k].items():
                v.join()
                await self.logger.info(f"Joined {t_k} thread ")

        await self.logger.info("All services stopped")
