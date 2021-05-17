
from testing_utils import load_submitter_local_log

import json
import time
import os

import asyncio
import sys
import pytest
from aiologger import Logger
sys.path.insert(0, "./")
from network_monitor.filters import present_protocols  # noqa
from network_monitor import Packet_Submitter  # noqa


async def consuming(filename: str):
    processed_queue = asyncio.Queue()
    packet_submitter: Packet_Submitter = Packet_Submitter(
        processed_queue,
        "http://localhost:5000/packets/",
        "./test/test_cases/local_submitter_out",
        5
    )

    packet_submitter_service_task: asyncio.ask = asyncio.create_task(
        packet_submitter.worker(None))

    async for f in load_submitter_local_log(filename):
        t = time.time()
        await processed_queue.put((t, f))

    await asyncio.sleep(2)
    packet_submitter_service_task.cancel()

    await asyncio.gather(packet_submitter_service_task, return_exceptions=True)
    assert processed_queue.qsize() == 0
    assert os.path.getsize(packet_submitter.get_output_filename()) > 0


@ pytest.mark.asyncio
@ pytest.mark.parametrize(
    ('filename'),
    (
        'test/test_cases/packet_parser_service/packet_parser_output_sample.lsp',
    )
)
async def test_consuming(filename: str):

    await consuming(filename)


async def compare_local_storage(filename: str):

    processed_queue = asyncio.Queue()
    packet_submitter: Packet_Submitter = Packet_Submitter(
        processed_queue,
        "http://localhost:5000/packets/",
        "./test/test_cases/local_submitter_out",
        5
    )

    packet_submitter_service_task: asyncio.ask = asyncio.create_task(
        packet_submitter.worker(None))

    async for f in load_submitter_local_log(filename):
        t = time.time()
        await processed_queue.put((t, f))

    await asyncio.sleep(5)
    packet_submitter_service_task.cancel()
    await asyncio.gather(packet_submitter_service_task, return_exceptions=True)
    assert processed_queue.qsize() == 0


# @ pytest.mark.asyncio
# @ pytest.mark.parametrize(
#     ('filename'),
#     (
#         'test/test_cases/packet_parser_service/packet_parser_output_sample.lsp',
#     )
# )
# async def test_compare_local_storage(filename: str):

#     # await compare_local_storage(filename)
#     ...


async def can_submit_packet(filename: str):
    processed_queue = asyncio.Queue()
    packet_submitter: Packet_Submitter = Packet_Submitter(
        processed_queue,
        "http://localhost:5050/packets/",
        "./test/test_cases/local_submitter_out",
        5
    )

    packet_submitter_service_task: asyncio.ask = asyncio.create_task(
        packet_submitter.worker(None))

    async for f in load_submitter_local_log(filename):
        t = time.time()
        await processed_queue.put((t, f))

    await asyncio.sleep(5)
    packet_submitter_service_task.cancel()
    await asyncio.gather(packet_submitter_service_task, return_exceptions=True)
    assert os.path.getsize(packet_submitter.get_output_filename()) == 0


@ pytest.mark.asyncio
@ pytest.mark.parametrize(
    ('filename'),
    (
        'test/test_cases/packet_parser_service/packet_parser_output_sample.lsp',
    )
)
async def test_can_submit_packete(filename: str):

    await can_submit_packet(filename)
