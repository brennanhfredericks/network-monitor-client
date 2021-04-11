import sys

sys.path.insert(0, "./")

import queue
import threading
import binascii
import os

from network_monitor.protocols import Packet_802_3, IPv4, TCP, UDP, ARP, IPv6
from network_monitor.filters import get_protocol, flatten_protocols
from test_load_data import load_file

# content of
def flatten_protocols_packets():
    ret = []
    for packet in load_file(
        ["raw_ipv6_output.lp", "raw_arp_output.lp", "raw_ipv4_output.lp"]
    ):
        out_packet = Packet_802_3(packet)
        out = flatten_protocols(out_packet)

        ret.append(isinstance(out, list) and len(out) > 0)

    return ret


def test_flatten_protocols_packets():

    assert all(flatten_protocols_packets()) == True