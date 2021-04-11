import queue
import threading
import time

import os
import base64
import json
import asyncio
import aiohttp
import aiofiles
import aiofiles.os
from aiohttp import ClientSession

from network_monitor.filters import flatten_protocols
from network_monitor.protocols import EnhancedJSONEncoder


class Submitter(object):
    """ responsible for submitting data and retrying  """

    def __init__(
        self,
        url: str,
        log_dir: str,
        max_buffer_size: int = 5,
        retryinterval: int = 60 * 5,
    ):

        self.url = url
        self.retryinterval = retryinterval
        self._logs_written = False
        # check
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

            self._log_dir = log_dir
            self._checked_for_logs = time.time()
        else:
            # check if files in directory. if files process and send to server
            self._log_dir = log_dir
            # process existing files
            asyncio.run(self._clear_logs())

            self._checked_for_logs = time.time()

        self.out_file = os.path.join(log_dir, f"out_{int(time.time())}.lsp")

        self.max_buffer_size = max_buffer_size
        self.__buffer = []

    async def _post_to_server(self, data, session: ClientSession):

        resp = await session.post(self.url, json=data)
        resp.raise_for_status()

        # write data to buffer

    async def _log(self, data):

        async with aiofiles.open(self.out_file, "a") as fout:
            await fout.write(json.dumps(data) + "\n")

        self._logs_written = True

    async def _logs_available(self):
        "os list dir"
        return [f for f in os.listdir(self._log_dir) if f.endswith(".lsp")]

    async def _clear_logs(self):
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
                        print("Monitor server not available")
                        # print("clear logs: aio exception: ", e)
                        break
                    except Exception as e:
                        print("clear logs: non aio exception: ", e)
                    else:
                        # only run when no exception occurs
                        await aiofiles.os.remove(infile)

    async def _post_or_disk(self, data, session):

        try:
            await self._post_to_server(data, session)
        except (aiohttp.ClientError, aiohttp.http_exceptions.HttpProcessingError) as e:
            # print("aio exception: ", e)
            await self._log(data)
        except Exception as e:

            print("non aio exception: ", e)

    async def _process(self):
        tasks = []

        async with ClientSession() as session:
            for data in self.__buffer:
                task = asyncio.create_task(self._post_or_disk(data, session))
                tasks.append(task)

            await asyncio.gather(*tasks)

        self.__buffer.clear()

    # submit data to server asynchronously
    async def submit(self, data):

        self.__buffer.append(data)
        time_now = time.time()
        if len(self.__buffer) > self.max_buffer_size:
            await self._process()
        elif (
            time_now - self._checked_for_logs > self.retryinterval
        ) and self._logs_written:

            await self._clear_logs()
            self._checked_for_logs = time.time()


class Packet_Submitter(object):
    """ class for storing and submitting packets"""

    def __init__(
        self,
        output_queue: queue.Queue,
        url: str,
        log_dir: str,
        retryinterval: int,
    ):
        self._data_queue = output_queue
        self._submitter = Submitter(url, log_dir, retryinterval=retryinterval)

    def _submit(self):

        while self._sentinal or not self._data_queue.empty():

            if not self._data_queue.empty():
                asyncio.run(self._submitter.submit(self._data_queue.get()))
            else:
                time.sleep(0.01)
        # write any data in buffer to disk
        asyncio.run(self._submitter._process())
        asyncio.run(self._submitter._clear_logs())

    def start(self):
        self._sentinal = True

        self._thread_handle = threading.Thread(
            target=self._submit, name="packet submitter", daemon=False
        )

        self._thread_handle.start()

    def stop(self):
        self._sentinal = False
        self._thread_handle.join()
