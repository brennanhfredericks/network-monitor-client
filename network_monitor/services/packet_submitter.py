import queue
import threading
import time

import os
import base64
import json
import asyncio
import aiohttp
import aiofiles
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
        re_try_interval: int = 60 * 5,
    ):

        self.url = url

        # check
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        else:
            # check if files in directory. if files process and send to server
            out_files = os.listdir(log_dir)
            if len(out_files) > 0:
                # process existing files
                ...

        self.out_file = os.path.join(log_dir, f"out_{int(time.time())}.lsp")

        self.max_buffer_size = max_buffer_size
        self.__buffer = []

    async def _serialize(self, origin_address, packet):
        return {
            "origin_address": origin_address,
            "packet": {p.identifier: p.serialize() for p in packet},
        }

    async def _post_to_server(self, data, session: ClientSession):

        resp = await session.post(self.url, json=data)
        resp.raise_for_status()

        # write data to buffer

    async def _log(self, data):

        async with aiofiles.open(self.out_file, "a") as fout:
            await fout.write(json.dumps(data) + "\n")

    async def _out_or_disk(self, origin_address, packet, session):

        k = await self._serialize(origin_address, flatten_protocols(packet))
        try:
            await self._post_to_server(k, session)
        except (aiohttp.ClientError, aiohttp.http_exceptions.HttpProcessingError) as e:
            print("aio exception: ", e)
            await self._log(k)
        except Exception as e:
            print("non aio exception: ", e)

        await asyncio.sleep(1)
        # print(k)

    async def _process(self):
        tasks = []

        async with ClientSession() as session:
            for d in self.__buffer:
                task = asyncio.create_task(self._out_or_disk(*d, session))
                tasks.append(task)

            await asyncio.gather(*tasks)

        self.__buffer.clear()

    # submit data to server asynchronously
    async def submit(self, data):

        self.__buffer.append(data)

        if len(self.__buffer) > self.max_buffer_size:
            await self._process()


class Packet_Submitter(object):
    """ class for storing and submitting packets"""

    def __init__(
        self,
        output_queue: queue.Queue,
        url: str = "http://127.0.0.1:5000/packets",
        log_dir="./logger_output/submitter/",
    ):
        self._data_queue = output_queue
        self._submitter = Submitter(url, log_dir)

    def _submit(self):
        re_try_timer = 60
        c = []
        while self._sentinal or not self._data_queue.empty():

            if not self._data_queue.empty():
                asyncio.run(self._submitter.submit(self._data_queue.get()))
            else:
                time.sleep(0.01)
        # write any data in buffer to disk
        # self._submitter._clear_buffer()

    def start(self):
        self._sentinal = True

        self._thread_handle = threading.Thread(
            target=self._submit, name="packet submitter", daemon=False
        )

        self._thread_handle.start()

    def stop(self):
        self._sentinal = False
        self._thread_handle.join()
