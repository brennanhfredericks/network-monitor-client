# include directory to project in path lookup


from aiologger import Logger, levels
from logging import Formatter
from typing import Dict, List
import sys
import asyncio
import os
import pytest

sys.path.insert(0, os.getcwd())
from network_monitor import Interface_Listener  # noqa

# create logger for testing
logger = Logger.with_default_handlers(
    name='single-interface',
    level=levels.LogLevel.FATAL,
    formatter=Formatter("%(asctime)s %(message)s")
)
raw_queue = asyncio.Queue()


async def listen_on_single_interface(interface_name: str):

    # interface listener service add raw binary data to queue

    # configure listerner service
    listener_service: Interface_Listener = Interface_Listener(
        interface_name, raw_queue)

    listener_service_task = asyncio.create_task(
        listener_service.worker(logger))

    # wait two seconds and check if data in queue
    await asyncio.sleep(1)

    assert raw_queue.qsize() > 0

    listener_service_task.cancel()

    await asyncio.gather(listener_service_task, return_exceptions=True)


def test_listen_on_single_interface():
    """
        check that we are able to listen on a single interface
    """
    asyncio.run(listen_on_single_interface("eth0"))

# @pytest.mark.xfail(raises=OSError)


async def listen_on_single_invalid_interface(interface_name: str):
    # configure listerner service
    with pytest.raises(OSError):
        listener_service: Interface_Listener = Interface_Listener(
            interface_name, raw_queue)

        listener_service_task = asyncio.create_task(
            listener_service.worker(logger))

        await asyncio.gather(listener_service_task, return_exceptions=False)


def test_listen_on_invalid_interface():

    asyncio.run(listen_on_single_invalid_interface("eth2"))
