
import time
import os
import sys
import json

import aiohttp
import aiofiles
import aiofiles.os
import asyncio


from aiohttp import ClientSession


from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.handlers.files import AsyncFileHandler
from aiologger.levels import LogLevel

from asyncio import Task, CancelledError
import queue
from aiofiles.threadpool import AsyncFileIO

from network_monitor.filters import flatten_protocols
from network_monitor.protocols import EnhancedJSONEncoder

from .service_manager import Service_Control

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

    async def set_logger(self, logger: Logger) -> None:
        self._logger = logger

    async def set_async_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        await self._logger.debug("Submitter injecting asynchronous loop")
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
        res = [f for f in os.listdir(self._log_dir) if f.endswith(".lsp")]
        return res

    async def _clear_logs(self) -> None:
        """
            check for existing logs and try post to server
        """

        logs: List[str] = self._logs_available()
        # maybe added functionality to post file
        if logs:
            # load from disk

            # open tcp session
            async with ClientSession() as session:
                # check if monitor server avalable
                resp = await session.get(self.url)

                if resp.status != 200:
                    # server unavailable
                    return

                # iterate over all logs
                for log in logs:
                    infile = os.path.join(self._log_dir, log)

                    try:
                        async with aiofiles.open(infile, "r") as fin:
                            tasks = []
                            async for line in fin:
                                data = json.loads(line)
                                task = self._loop.create_task(
                                    self._post_to_server(data, session)
                                )
                                tasks.append(task)

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
            # await self._logger.warning(f"something wrong with remote storage: {e}")
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
        await self._logger.debug("new data")
        # internal buffer
        if len(self._buffer) > self.max_buffer_size:
            await self._logger.debug("processing internal buffer")
            await self._process()
        elif (
            time_now - self._checked_for_logs > self.retryinterval
        ) and self._logs_written:
            await self._logger.debug("clearing local logs")
            self._loop.create_task(self._clear_logs())

            self._checked_for_logs = time.time()


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
        # retrieve running loop
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()

        # could be used to inject other asynchronouse task
        service_control.loop = loop

        logger = Logger(name=__name__, level=LogLevel.INFO)

        # create handles
        stream_handler = AsyncStreamHandler(
            stream=sys.stderr
        )

        logger.add_handler(stream_handler)

        try:

            file_handler = AsyncFileHandler(
                os.path.join(self.log_directory, "packet_submitter.log")
            )
            logger.add_handler(file_handler)

        except Exception as e:
            await logger.exception("error creating AsycFileHandler: {e}")
            service_control.error = True
        else:

            # configure submitter logger
            await self._submitter.set_logger(logger)

            # configure asynchronous loop to add other task such as clearing old logs
            await self._submitter.set_async_loop(loop)

            while service_control.sentinal:
                # print(time.monotonic())
                try:
                    #s = time.monotonic()
                    # wait for processed data from the packer service queue
                    data: Dict[str, Dict[str, Union[str, int]]
                               ] = service_control.in_channel.get(timeout=1)

                    await logger.debug(f"Data: {data}\n")

                    # add another corotine here that only adds packet async consumer
                    # i.e here we produce data
                    await self._submitter.process(data)

                    service_control.in_channel.task_done()
                    #print("packet parser time diff: ", time.monotonic()-s)
                    service_control.stats["packets_submitted"] += 1
                except queue.Empty:
                    pass
                except CancelledError as e:
                    # clear internal buffer
                    await logger.info("clearing internal buffer")
                    await self._submitter.flush()
                    raise e
                except Exception as e:
                    await logger.exception(f"An error occured in packet submitter service {e}")
