import queue
import threading
import binascii
import os
import time
import sys

from network_monitor.protocols import (
    Packet_802_2,
    Packet_802_3,
    AF_Packet,
    TCP,
    IPv4,
    Protocol_Parser,
)
from network_monitor import Packet_Filter, Filter
from network_monitor.filters import present_protocols
from test_load_data import load_filev2


def start_filter():
    packet_filter = Packet_Filter()

    # create Filter to filter all packets send by application to monitor services
    t_filter = Filter(
        "application post traffic", [{AF_Packet: {"ifname": "lo"}}, {TCP: {}}]
    )
    print(Protocol_Parser.get_protocol_by_class_name("AF_Packet"))
    packet_filter.register(t_filter)

    for i, (origin_address, packet) in enumerate(
        load_filev2(
            "raw2_protocols_1617213286_IPv4_IPv6_UDP_TCP_ARP_ICMP_ICMPv6_IGMP_LLDP_CDP.lp",
            log_dir="./remote_data",
        )
    ):

        if origin_address["protocol"] > 1500:
            out = Packet_802_3(packet)
        else:
            out = Packet_802_2(packet)

        if i > 10:

            break
        # print(af_packet, out)


def test_filter():
    start_filter()
    assert False
