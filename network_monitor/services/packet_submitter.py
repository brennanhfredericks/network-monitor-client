
import time
import os
import sys
import json

import aiohttp
import aiofiles
import aiofiles.os
import asyncio
from enum import Enum
import functools

from aiohttp import ClientSession, ClientTimeout


from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.handlers.files import AsyncFileHandler
from aiologger.levels import LogLevel

from asyncio import Task, CancelledError
import queue
from aiofiles.threadpool import AsyncFileIO


from .service_manager import Service_Control

from typing import List, Any, Optional, Union, Dict


class Submitter(object):
    """ responsible for submitting data and retrying  """

    def __init__(
        self,
        url: str,
        log_dir: str,
        timeout: int = 300,
        retryinterval: int = 600,
    ) -> None:

        self.url: str = url
        self.retryinterval: int = retryinterval

        self._session_timeout: aiohttp.ClientTimeout = ClientTimeout(
            total=timeout)

        self._session: Optional[ClientSession] = None
        self._outfile: Optional[AsyncFileIO] = None
        self._logs_written: bool = False

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._data_channel: Optional[asyncio.Queue] = None

        self._logger: Optional[Logger] = None
        #self._checked_for_logs: Optional[float] = None

        # check
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            self._log_dir: str = log_dir

            #self._checked_for_logs = time.time()
        else:
            # check if files in directory. if files process and send to server
            self._log_dir = log_dir
            # check for existing logs when asynchronous loop is set

    async def set_logger(self, logger: Logger) -> None:
        self._logger = logger

    async def set_async_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def _remote_storage(self, data: Dict[str, Union[str, int]]):

        resp = await self._session.post(self.url, json=data, timeout=1)

        # if fail raise ClientResponseError
        resp.raise_for_status()

    async def _local_storage(self, data: Dict[str, Union[str, int]]):
        await self._outfile.write(json.dumps(data) + "\n")

    async def _close_mode(self) -> None:
        # when submitter is closed we know all is closed

        if self._session is not None:
            await self._session.close()
            self._session = None

        if self._outfile is not None:

            # make sure the buffer is clear
            await self._outfile.flush()
            await self._outfile.close()

            self._outfile = None

    async def _change_storage_mode(self):

        if self._storage_mode == self._remote_storage:
            # close remote
            await self._close_mode()
            # create new output file
            res = await self._configure_outfile()
            # switch to local storage
            if res:
                self._storage_mode = self._local_storage

        elif self._storage_mode == self._local_storage:
            # switch to remote storage
            await self._close_mode()

            res = await self._configure_session()

            if res:
                self._storage_mode = self._remote_storage
                #
                # load local files clear them out
        else:
            # should never reach this state
            await self._logger.exception(
                f"storage mode unknown: {self._storage_mode}"
            )

            self._storage_mode = self._remote_storage

    async def _storage(self, data: Dict[str, Union[str, int]]):

        try:

            await self._storage_mode(data)

        except (aiohttp.ClientError,
                aiohttp.http_exceptions.HttpProcessingError)as e:
            await self._logger.exception(f"remote storage exception: {e}")
            await self._change_storage_mode()
            await self._storage_mode(data)
        except Exception as e:
            await self._logger.exception(f"local store exception: {e}")
            # create a new file for logging
            await self._configure_outfile()

    async def _configure_outfile(self) -> bool:

        outfile: str = os.path.join(
            self._log_dir, f"{int(time.time())}.lsp"
        )

        try:
            self._outfile = await aiofiles.open(outfile, "a")
        except Exception as e:
            self._logger.exception(f"Unable to create local storage file: {e}")
            self._outfile = None
            return False

        return True

    async def _configure_session(self) -> bool:

        # need specify connection with the approriate header configuration

        try:

            self._session = ClientSession(timeout=self._session_timeout)
            resp = await self._session.get(self.url, timeout=1)
            assert resp.status == 200
        except Exception as e:
            self._logger.info(f"monitor server unavailable")
            # free resources
            await self._session.close()
            self._session = None
            return False

        return True

    async def process(self, data_channel: asyncio.Queue) -> None:

        # check if monitor server is available by call remote get()

        res: bool = await self._configure_session()

        # if server available call remote storage
        if res:
            self._storage_mode = self._remote_storage
        else:
            await self._configure_outfile()
            self._storage_mode = self._local_storage

        while True:
            try:
                data: Dict[str, Dict[str, Union[str, int]]] = await data_channel.get()
            except asyncio.CancelledError as e:
                # cancel operation close out any open operation.
                await self._close_mode()
                await self._logger.info(f"submitter process has been closed")
                raise e
            else:
                data["Info"]["Submitted_Timestamp"] = time.time()

                await self._storage(data)

                # await self._logger.info(f"size: {data_channel.qsize()}")
                data_channel.task_done()


class Packet_Submitter(object):
    """ class for storing and submitting packets"""

    def __init__(
        self,
        remote_metadata_storage: str,
        local_metadata_storage: str,
        log_directory: str,
        retry_interval: int,
    ):

        # configure submitter that
        self._submitter: Submitter = Submitter(
            remote_metadata_storage,
            local_metadata_storage,
            retryinterval=retry_interval
        )

        self.log_directory = log_directory

    def get_output_filename(self) -> str:
        return self._submitter.output_filename()

    async def worker(self, service_control: Service_Control) -> None:

        # loop timeout to stop checking for data when queue is empty
        loop_timeout: float = 0.5

        # retrieve running loop
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()

        # could be used to inject other asynchronouse task
        service_control.loop = loop

        # configure asynchronous loop to add other task such as clearing old logs
        await self._submitter.set_async_loop(loop)

        logger = Logger(name=__name__, level=LogLevel.INFO)

        # create handles
        stream_handler = AsyncStreamHandler(
            stream=sys.stderr
        )

        logger.add_handler(stream_handler)

        try:
            # could fail due to permission issue
            file_handler = AsyncFileHandler(
                os.path.join(self.log_directory, "packet_submitter.log")
            )

        except Exception as e:

            await logger.exception("error creating AsycFileHandler: {e}")
            # inform main async loop that this thread errored out
            service_control.error = True

            # exit worker coroutine and allow thread exit normally
            return
        else:
            logger.add_handler(file_handler)
            # configure submitter logger
            await self._submitter.set_logger(logger)

        # internal create coroutine process task
        data_channel: asyncio.Queue = asyncio.Queue()

        process_task = loop.create_task(

            self._submitter.process(data_channel), name="process")

        while service_control.sentinal:

            try:

                # wait for processed data from the packer service queue
                data: Dict[str, Dict[str, Union[str, int]]
                           ] = service_control.in_channel.get_nowait()
            except queue.Empty:
                # queue empty, timeout before checking again
                await asyncio.sleep(loop_timeout)

            except CancelledError as e:
                # coroutine function cancelled
                raise e

            except Exception as e:
                await logger.exception(f"An error occured in packet submitter service {e}")

            else:
                # add data to submitter queue with out blocking. queue is growable
                await data_channel.put(data)

                # inform queue task has been completed
                service_control.in_channel.task_done()

                # status updated
                service_control.stats["packets_submitted"] += 1

        # wait for queue to clear if there are still items available

        await data_channel.join()
        # close process_task running in continuous True loop which raises Cancel error
        process_task.cancel()

        await asyncio.gather(process_task, return_exceptions=True)
