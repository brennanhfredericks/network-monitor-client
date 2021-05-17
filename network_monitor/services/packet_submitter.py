
import time

import os
import base64
import json

import aiohttp
import aiofiles
import aiofiles.os
import asyncio
import io

from aiohttp import ClientSession
from aiologger import Logger, formatters

from asyncio import Task, Queue, CancelledError
from aiofiles.threadpool import AsyncFileIO

from network_monitor.filters import flatten_protocols
from network_monitor.protocols import EnhancedJSONEncoder

from typing import List, Any, Optional, Union, Dict


class Submitter(object):
    """ responsible for submitting data and retrying  """

    def __init__(
        self,
        url: str,
        log_dir: str,
        max_buffer_size: int = 5,
        retryinterval: int = 300,
    ) -> None:

        self.url: str = url
        self.retryinterval: int = retryinterval
        self._logs_written: bool = False
        self._tasks: List[asyncio.Task] = []
        # check
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

            self._log_dir: str = log_dir
            self._checked_for_logs: float = time.time()
        else:
            # check if files in directory. if files process and send to server
            self._log_dir = log_dir
            # process existing files

            self._tasks.append(asyncio.create_task(self._clear_logs()))

            self._checked_for_logs = time.time()

        self.out_file: str = os.path.join(
            log_dir, f"out_{int(time.time())}.lsp")

        self.max_buffer_size: int = max_buffer_size
        self.__buffer: Dict[str, Dict[str, Union[str, int]]] = []

    async def set_logger(self, logger: Optional[Logger] = None) -> None:
        self.logger: Logger = logger

    async def _post_to_server(self, data, session: ClientSession) -> None:

        # return context manager
        resp = await session.post(self.url, json=data)
        # if fail raise ClientResponseError
        resp.raise_for_status()

    async def _local_storage(self, data: Dict[str, Dict[str, Union[str, int]]], fout: AsyncFileIO) -> None:
        await fout.write(json.dumps(data) + "\n")

        self._logs_written = True

    async def _logs_available(self) -> List[str]:
        "os list dir"
        return [f for f in os.listdir(self._log_dir) if f.endswith(".lsp")]

    async def _clear_logs(self) -> None:
        "remove logs and try to post"

        logs = await self._logs_available()
        # maybe added functionality to post file
        if logs:
            # load from disk
            tasks = []
            async with ClientSession() as session:

                for log in logs:
                    infile = os.path.join(self._log_dir, log)

                    async with aiofiles.open(infile, "r") as fin:
                        async for line in fin:
                            data = json.loads(line)
                            task = asyncio.create_task(
                                self._post_to_server(data, session)
                            )
                            tasks.append(task)
                    try:
                        await asyncio.gather(*tasks)
                    except (
                        aiohttp.ClientError,
                        aiohttp.http_exceptions.HttpProcessingError,
                    ) as e:
                        if self.logger is not None:
                            self.logger.warning(
                                f"remote storage not available: {e}")
                    except Exception as e:
                        if self.logger is not None:
                            await self.logger.exception(f"exception when trying to clear logs: {e}")
                    else:
                        # only run when no exception occurs
                        await aiofiles.os.remove(infile)

    async def _post_or_disk(self, data, session, fout: AsyncFileIO) -> None:

        try:
            await self._post_to_server(data, session)
        except (aiohttp.ClientError, aiohttp.http_exceptions.HttpProcessingError) as e:
            # await self.logger.warning(f"something wrong with remote storage: {e}")
            await self._local_storage(data, fout)
        except Exception as e:
            if self.logger is not None:
                await self.logger.exception(f"exception when trying to switch between post_or_disk: {e}")

    async def _process(self) -> None:
        tasks: List[Task] = []

        async with ClientSession() as session:
            async with aiofiles.open(self.out_file, "a") as fout:
                for data in self.__buffer:
                    data["Info"]["Submitter_Timestamp"] = time.time()
                    task: Task = asyncio.create_task(
                        self._post_or_disk(data, session, fout)
                    )
                    tasks.append(task)

                await asyncio.gather(*tasks)

        # clear out internal buffer
        self.__buffer.clear()

    # submit data to server asynchronously
    async def process(self, data: Dict[str, Dict[str, Union[str, int]]]) -> None:

        # add data to internal buffer
        self.__buffer.append(data)
        time_now = time.time()

        if len(self.__buffer) > self.max_buffer_size:
            await self._process()
        elif (
            time_now - self._checked_for_logs > self.retryinterval
        ) and self._logs_written:

            self._tasks.append(asyncio.create_task(self._clear_logs()))
            self._checked_for_logs = time.time()


class Packet_Submitter(object):
    """ class for storing and submitting packets"""

    def __init__(
        self,
        processed_queue: Queue,
        url: str,
        log_dir: str,
        retryinterval: int,
    ):
        self.processed_data_queue: Queue = processed_queue

        self._submitter: Submitter(url, log_dir) = Submitter(
            url, log_dir, retryinterval=retryinterval)

    async def worker(self, logger: Optional[Logger] = None):
        await self._submitter.set_logger(logger)
        while True:
            try:

                # wait for processed data from the packer service queue
                data: Dict[str, Dict[str, Union[str, int]]] = await self.processed_data_queue.get()

                await self._submitter.process(data)

                self.processed_data_queue.task_done()

            except CancelledError as e:
                await asyncio.gather(*self._submitter._tasks, return_exceptions=True)
                print("packet submitter service cancelled", e)
                raise e
            except Exception as e:
                if logger is not None:
                    await logger.exception(f"submitter_exception: {e}")
