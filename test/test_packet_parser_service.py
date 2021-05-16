
from testing_utils import load_raw_listener_service_output, load_packet_parser_comparison_values
import os
import asyncio
import sys
import pytest
import itertools

sys.path.insert(0, "./")


from network_monitor.filters import get_protocol, present_protocols  # noqa
from network_monitor.protocols import (  # noqa
    Packet_802_3,
    Packet_802_2,
)


# load data from file
# to iterate and async generator, you need adn async for loop
async def parsing_raw_data(filename: str, filename_present_protocols: str):

    # async for p_protos, (af_address, raw_bytes) in itertools.zip_longest(
    #         load_raw_listener_service_ouput(filename),
    #         load_packet_parser_comparison_values(filename_present_protocols)):

    lrlso = load_raw_listener_service_output(filename)
    lppcv = load_packet_parser_comparison_values(filename_present_protocols)
    while True:

        try:
            af_packet, raw_bytes = await lrlso.__anext__()
            comparison = await lppcv.__anext__()
        except StopAsyncIteration as e:
            break
        else:
            print(af_packet, comparison)
            if af_packet["Ethernet_Protocol_Number"] >= 0 and af_packet["Ethernet_Protocol_Number"] <= 1500:

                # logical link control (LLC) Numbers
                out_packet = Packet_802_2(raw_bytes)
            else:
                # check whether WIFI packets are different from ethernet packets

                out_packet = Packet_802_3(raw_bytes)

            res = present_protocols(out_packet)

            assert res == comparison


@ pytest.mark.parametrize(
    ("filename", "filename_present_protocols"),
    (
        ("test/test_cases/raw_interface_service_capture/raw_sample.lp",
         "test/test_cases/raw_interface_service_capture/raw_sample_present_protocols.lp"),
        ("test/test_cases/raw_interface_service_capture/raw_sample_dup.lp",
         "test/test_cases/raw_interface_service_capture/raw_sample_present_protocols.lp")
    )
)
def test_parsing_raw_data(filename: str, filename_present_protocols: str):

    asyncio.run(parsing_raw_data(filename, filename_present_protocols))
