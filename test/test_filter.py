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
    t0_filter = Filter(
        "test0",
        {"AF_Packet": {"ifname": "lo"}},
    )

    t1_filter = Filter(
        "test1",
        {"TCP": {}},
    )

    t2_filter = Filter(
        "test2",
        [{"IPv4": {}}, {"UDP": {}}],
    )

    packet_filter.register(t0_filter)
    # packet_filter.register(t1_filter)
    # packet_filter.register(t2_filter)

    for i, (af_packet, raw_bytes) in enumerate(
        load_filev2(
            "raw2_protocols_1617213286_IPv4_IPv6_UDP_TCP_ARP_ICMP_ICMPv6_IGMP_LLDP_CDP.lp",
            log_dir="./remote_data",
        )
    ):

        if af_packet["protocol"] > 1500:
            out_packet = Packet_802_3(raw_bytes)
        else:
            out_packet = Packet_802_2(raw_bytes)
        res = packet_filter.apply(af_packet, out_packet)

        if res is None:
            continue
        else:
            assert af_packet["ifname"] != "lo"


def test_filter():
    start_filter()
