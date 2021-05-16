
from testing_utils import load_raw_listener_service_ouput
import os
import asyncio
import sys
import pytest

sys.path.insert(0, "./")


from network_monitor.filters import get_protocol, present_protocols  # noqa
from network_monitor.protocols import (  # noqa
    Packet_802_3,
    Packet_802_2,
)


# load data from file
# to iterate and async generator, you need adn async for loop
async def parsing_raw_data(filename: str):

    async for af_address, raw_bytes in load_raw_listener_service_ouput(filename):
        print(af_address)
        # print(raw_bytes)

    # can cause issue if only one case availabel due to interpolation
    assert False


@pytest.mark.parametrize(
    ("filename"),
    (
        ("test/test_cases/raw_interface_service_capture/raw_sample.lp"),
        ("test/test_cases/raw_interface_service_capture/raw_sample_dup.lp")
    )
)
def test_parsing_raw_data(filename: str):

    asyncio.run(parsing_raw_data(filename))
