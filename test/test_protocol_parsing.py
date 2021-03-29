import sys

sys.path.insert(0, "../")

import queue
import threading
import binascii
import os

from network_monitor.protocols import (
    Packet_802_2,
    Packet_802_3,
    IPv4,
    TCP,
    UDP,
    ARP,
    IPv6,
)
from network_monitor.filters import get_protocol
from test_load_data import load_file


def ipv4_packets():
    """ test ipv4 parsing """

    for packet in load_file(
        "raw_protocols_1616955106_IPv4_IPv6.lp", log_dir="./remote_data"
    ):

        print(packet)
        # if packet.proto > 1500:
        #     Packet_802_3(packet)
        break


def test_ipv4_protocol():

    assert ipv4_packets() == False
