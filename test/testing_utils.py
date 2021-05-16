from typing import List
import base64
import json
import os
import asyncio
import pytest
import aiofiles
import sys
import time
sys.path.insert(0, "./")

from network_monitor.filters import get_protocol, present_protocols  # noqa
from network_monitor.protocols import (  # noqa
    Packet_802_3,
    Packet_802_2,
)


async def load_submitter_local_log(filename):

    if not os.path.exists(filename):
        raise ValueError("invalid filename %s" % filename)

    async with aiofiles.open(filename, "r") as fin:
        async for line in fin:
            yield json.loads(line)


def interface_listener_simulate(filename: str, queue: asyncio.Queue):
    i = 0
    with open(filename, "r") as fin:
        while True:
            af_packet = fin.readline()
            if len(af_packet) == 0:
                break

            raw_bytes = fin.readline()

            af_packet = json.loads(af_packet)
            raw_bytes = base64.b64decode(raw_bytes)

           # yield af_packet, packet
            cap_time = time.time()

            queue.put_nowait((cap_time, (af_packet, raw_bytes)))
            # i += 1
            # if i == 10:
            #     break
    #assert False


async def load_raw_listener_service_output(filename: str):
    """load file and return raw pack bytes"""

    if not os.path.exists(filename):
        raise ValueError(f"{filename} does not exist")

    async with aiofiles.open(filename, "r") as fin:
        while True:
            af_packet = await fin.readline()
            if len(af_packet) == 0:
                break

            raw_bytes = await fin.readline()

            af_packet = json.loads(af_packet)
            packet = base64.b64decode(raw_bytes)

            yield af_packet, packet


async def load_packet_parser_comparison_values(filename: str) -> List[int]:

    async with aiofiles.open(filename, "r") as fin:
        async for line in fin:
            protos = [int(i) for i in line.split(",")]
            yield protos


async def generate_packet_parser_comparison_values(filename: str):
    f = filename.split(".")[0]
    async with aiofiles.open(f"{f}_present_protocols.lp", "w") as fout:

        async for af_packet, raw_bytes in load_raw_listener_service_output(filename):

            if af_packet["Ethernet_Protocol_Number"] >= 0 and af_packet["Ethernet_Protocol_Number"] <= 1500:

                # logical link control (LLC) Numbers
                out_packet = Packet_802_2(raw_bytes)
            else:
                # check whether WIFI packets are different from ethernet packets

                out_packet = Packet_802_3(raw_bytes)

            res = present_protocols(out_packet)

            await fout.write(",".join(str(i) for i in res) + "\n")

# if __name__ == "__main__":

#     asyncio.run(generate_packet_parser_comparison_values(
#         "test/test_cases/raw_interface_service_capture/raw_sample.lp"))
