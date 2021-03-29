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
    res = []
    for packet in load_file(
        "raw_protocols_1616955106_IPv4_IPv6.lp", log_dir="./remote_data"
    ):

        out_packet = Packet_802_3(packet)

        out_proto = get_protocol(out_packet, IPv4)

        if out_proto is None:
            continue

        else:
            res.append(out_proto.identifier == IPv4.identifier)

    return res


def test_ipv4_protocol():

    assert all(ipv4_packets()) == True
