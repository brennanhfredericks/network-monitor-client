import base64
import json
import os
import asyncio
import pytest
import aiofiles


async def load_submitter_local_log(filename):

    if not os.path.exists(filename):
        raise ValueError("invalid filename %s" % filename)

    async with aiofiles.open(filename, "r") as fin:
        async for line in fin:
            yield json.loads(line)


async def load_raw_listener_service_ouput(filename: str):
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


async def generate_packet_parser_comparison_values(filename: str):

    async for af_packet, raw_bytes in load_raw_listener_service_ouput(filename):
        # print(af_address)
        ...


if __name__ == "__main__":

    asyncio.run(generate_packet_parser_comparison_values(
        "test/test_cases/raw_interface_service_capture/raw_sample.lp"))
