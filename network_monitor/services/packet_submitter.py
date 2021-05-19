
import time
import os

import json

import aiohttp
import aiofiles
import aiofiles.os
import asyncio


from aiohttp import ClientSession

from logging import Formatter
from aiologger import Logger

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
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._logger: Optional[Logger] = None
        self._checked_for_logs: Optional[float] = None

        # check
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

            self._log_dir: str = log_dir
            self._checked_for_logs = time.time()
        else:
            # check if files in directory. if files process and send to server
            self._log_dir = log_dir
            # check for existing logs when asynchronous loop is set

        self.out_file: str = os.path.join(
            log_dir, f"out_{int(time.time())}.lsp")

        self.max_buffer_size: int = max_buffer_size
        self._buffer: Dict[str, Dict[str, Union[str, int]]] = []

    def output_filename(self) -> str:
        return self.out_file

    def set_logger(self, logger: Logger) -> None:
        self._logger = logger

    def set_async_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._loop.create_task(self._clear_logs())
        self._checked_for_logs = time.time()

    async def _post_to_server(self, data, session: ClientSession) -> None:

        # return context manager
        resp = await session.post(self.url, json=data)
        # if fail raise ClientResponseError
        resp.raise_for_status()

    async def _local_storage(self, data: Dict[str, Dict[str, Union[str, int]]], fout: AsyncFileIO) -> None:
        await fout.write(json.dumps(data) + "\n")

        self._logs_written = True

    def _logs_available(self) -> List[str]:
        "os list dir"
        return [f for f in os.listdir(self._log_dir) if f.endswith(".lsp")]

    async def _clear_logs(self) -> None:
        """
            check for existing logs and try post to server
        """

        logs: List[str] = self._logs_available()
        # maybe added functionality to post file
        if logs:
            # load from disk
            tasks = []

            # open tcp session
            async with ClientSession() as session:

                # iterate over all logs
                for log in logs:
                    infile = os.path.join(self._log_dir, log)

                    async with aiofiles.open(infile, "r") as fin:
                        async for line in fin:
                            data = json.loads(line)
                            task = self._loop.create_task(
                                self._post_to_server(data, session)
                            )
                            tasks.append(task)
                    try:
                        await asyncio.gather(*tasks)
                    except (
                        aiohttp.ClientError,
                        aiohttp.http_exceptions.HttpProcessingError,
                    ) as e:

                        self._logger.warning(
                            f"remote storage not available: {e}")
                    except Exception as e:

                        await self._logger.exception(f"exception occured when trying to clear logs: {e}")
                    else:
                        # only run when no exception occurs
                        await aiofiles.os.remove(infile)

    async def _post_or_disk(self, data: Dict[str, Dict[str, Union[str, int]]], session: ClientSession, fout: AsyncFileIO) -> None:

        try:
            # try to post data to the service
            await self._post_to_server(data, session)
        except (aiohttp.ClientError, aiohttp.http_exceptions.HttpProcessingError) as e:
            # server not available write data to file
            await self._local_storage(data, fout)
            await self._logger.warning(f"something wrong with remote storage: {e}")
        except Exception as e:

            await self._logger.exception(f"exception occured when trying to switch between post_or_disk: {e}")

    async def _process(self) -> None:
        tasks: List[Task] = []

        try:
            async with ClientSession() as session:
                async with aiofiles.open(self.out_file, "a") as fout:
                    for data in self._buffer:
                        data["Info"]["Submitter_Timestamp"] = time.time()
                        task: Task = self._loop.create_task(
                            self._post_or_disk(data, session, fout)
                        )
                        tasks.append(task)

                    await asyncio.gather(*tasks)
        except Exception as e:
            await self._logger.exception(f"exception occured when trying to process internal buffer: {e}")
        else:
            # clear out internal buffer
            self._buffer.clear()

    async def flush(self):
        if len(self._buffer) > 0:
            await self._process()

    # submit data to server asynchronously
    async def process(self, data: Dict[str, Dict[str, Union[str, int]]]) -> None:

        # add data to internal buffer
        self._buffer.append(data)
        time_now = time.time()

        # internal buffer
        if len(self._buffer) > self.max_buffer_size:
            await self._process()
        elif (
            time_now - self._checked_for_logs > self.retryinterval
        ) and self._logs_written:

            self._loop.create_task(self._clear_logs())

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

        # configure submitter that
        self._submitter: Submitter = Submitter(
            url,
            log_dir,
            retryinterval=retryinterval
        )

    def get_output_filename(self) -> str:
        return self._submitter.output_filename()

    async def worker(self):
        # retrieve running loop
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()

        out_format = Formatter(
            "%(asctime)s:%(name)s:%(levelname)s"
        )

        logger = Logger.with_default_handlers(
            name=__name__,
            formatter=out_format
        )

        # configure submitter logger
        self._submitter.set_logger(logger)

        # configure asynchronous loop
        self._submitter.set_async_loop(loop)

        while True:
            try:

                # wait for processed data from the packer service queue
                data: Dict[str, Dict[str, Union[str, int]]] = await self.processed_data_queue.get()

                await self._submitter.process(data)

                self.processed_data_queue.task_done()

            except CancelledError as e:
                # clear internal buffer
                await self._submitter.flush()
                raise e
            except Exception as e:
                await logger.exception(f"An error occured in packet submitter service: {e}")
