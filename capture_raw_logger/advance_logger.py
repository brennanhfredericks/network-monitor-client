
from typing import Optional, Dict, Union
from aiologger import Logger
import json
import aiofiles
import collections
import time
import os
import asyncio
import base64
import sys
sys.path.insert(0, "../")


from network_monitor.filters import get_protocol, present_protocols  # noqa
from network_monitor.protocols import (  # noqa
    AF_Packet,
    Packet_802_3,
    Packet_802_2
)
from network_monitor import (  # noqa
    Interface_Listener,
    Packet_Parser
)

# write to tmp file and replace with os.replace


async def _log_interface_listener_output(queue):
    start_time = int(time.time())
    log_dir = "./test/data/interface_listener_output/"
    report_interval = 5

    fname = f"interface_listener_output_{start_time}.lp"

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    tracker = collections.Counter()
    last_report_time = time.time()

    async with aiofiles.open(os.path.join(log_dir, fname), "w") as fout:
        while True:
            try:
                _, (raw_bytes, address) = await queue.get()

                af_packet = AF_Packet(address)

                if af_packet.Ethernet_Protocol_Number > 1500:
                    out_packet = Packet_802_3(raw_bytes)
                else:
                    out_packet = Packet_802_2(raw_bytes)

                await fout.write(json.dumps(af_packet.serialize()) + "\n")
                r_raw_bytes = base64.b64encode(raw_bytes).decode("utf-8")

                await fout.write(r_raw_bytes + "\n")

                queue.task_done()

                for identifier in present_protocols(out_packet):
                    tracker[identifier] += 1

                now = time.time()
                if now - last_report_time > report_interval:
                    __tracker = {k: v for k, v in tracker.items()}
                    last_report_time = now
                    print("queue size: ", queue.qsize())
                    print("Tracker: ", __tracker)
            except asyncio.CancelledError as e:

                print("log service cancelled", e)

                raise e


async def _log_packet_parser_output_no_filter(queue):
    start_time = int(time.time())
    log_dir = "./test/data/packet_parser_output/"
    report_interval = 5

    fname = f"packet_parser_output_{start_time}.lp"

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    tracker = collections.Counter()
    last_report_time = time.time()

    async with aiofiles.open(os.path.join(log_dir, fname), "w") as fout:
        while True:
            try:
                data = await queue.get()

                await fout.write(json.dumps(data) + "\n")

                queue.task_done()

                for identifier in data:
                    tracker[identifier] += 1

                now = time.time()
                if now - last_report_time > report_interval:
                    __tracker = {k: v for k, v in tracker.items()}
                    last_report_time = now
                    print("queue size: ", queue.qsize())
                    print("Tracker: ", __tracker)
            except asyncio.CancelledError as e:

                print("log service cancelled", e)

                raise e


async def log_raw_packets(
    interfacename: str,

):

    raw_queue = asyncio.Queue()

    logger = Logger.with_default_handlers()

    # start network listener
    listener_service = Interface_Listener(interfacename, raw_queue)

    listener_service_task: asyncio.Task = asyncio.create_task(
        listener_service.worker(logger), name="listener-service-task")

    log_task = asyncio.create_task(
        _log_interface_listener_output(raw_queue))
    await asyncio.sleep(600)
    listener_service_task.cancel()
    print("listener task cancelled")
    await raw_queue.join()

    await asyncio.sleep(2)
    log_task.cancel()
    print("log task cancelled")
    await asyncio.gather(listener_service_task, log_task, return_exceptions=True)


async def log_processed_packets(interfacename: str):

    raw_queue = asyncio.Queue()
    processed_queue = asyncio.Queue()

    logger = Logger.with_default_handlers()

    # start network listener
    listener_service = Interface_Listener(interfacename, raw_queue)

    listener_service_task: asyncio.Task = asyncio.create_task(
        listener_service.worker(logger), name="listener-service-task")

    packet_parser = Packet_Parser(raw_queue, processed_queue)

    packet_parser_service_task: asyncio.Task = asyncio.create_task(
        packet_parser.worker(logger), name="packet-service-task"
    )

    log_task = asyncio.create_task(
        _log_packet_parser_output_no_filter(processed_queue))
    await asyncio.sleep(600)
    listener_service_task.cancel()
    print("listener task cancelled")
    await raw_queue.join()
    packet_parser_service_task.cancel()

    await processed_queue.join()

    await asyncio.sleep(2)
    log_task.cancel()
    print("log task cancelled")
    await asyncio.gather(listener_service_task, packet_parser_service_task, log_task, return_exceptions=True)

if __name__ == "__main__":

    asyncio.run(log_processed_packets(
        "eth0"
    ))
