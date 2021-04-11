import sys

sys.path.insert(0, "./")

import queue
import threading
import binascii
import os
import time
import json

from network_monitor.protocols import (
    Packet_802_2,
    Packet_802_3,
    AF_Packet,
)
from network_monitor import Packet_Submitter, Packet_Filter, Filter
from network_monitor.filters import present_protocols
from test_load_data import load_filev2

url = "http://127.0.0.1:5000/packets"
local = "./logs/submitter_service/"
retryinterval = 300


def submitter_logged_file():
    feeder = queue.Queue()

    t0_filter = Filter(
        "test0",
        {"AF_Packet": {"ifname": "lo"}},
    )

    packet_filter = Packet_Filter()
    packet_filter.register(t0_filter)

    packet_submitter = Packet_Submitter(feeder, url, local, retryinterval)

    packet_submitter.start()
    for i, (af_packet, raw_packet) in enumerate(
        load_filev2(
            "raw2_protocols_1617213286_IPv4_IPv6_UDP_TCP_ARP_ICMP_ICMPv6_IGMP_LLDP_CDP.lp",
            log_dir="./test/remote_data",
        )
    ):

        if af_packet["protocol"] > 1500:
            out = Packet_802_3(raw_packet)
        else:
            out = Packet_802_2(raw_packet)

        res = packet_filter.apply(af_packet, out)

        if res is None:
            continue
        else:
            feeder.put(res)

    packet_submitter.stop()

    with open(packet_submitter._submitter.out_file, "r") as fin:
        for line in fin:
            data = json.loads(line)

            res = t0_filter.apply(data)
            assert res == False


def test_submitter_logger():

    submitter_logged_file()


def start_submitter():

    feeder = queue.Queue()

    t0_filter = Filter(
        "test0",
        {"AF_Packet": {"ifname": "lo"}},
    )
    packet_filter = Packet_Filter()
    packet_filter.register(t0_filter)

    packet_submitter = Packet_Submitter(feeder, url, local, retryinterval)

    packet_submitter.start()
    for i, (af_packet, raw_packet) in enumerate(
        load_filev2(
            "raw2_protocols_1617213286_IPv4_IPv6_UDP_TCP_ARP_ICMP_ICMPv6_IGMP_LLDP_CDP.lp",
            log_dir="./test/remote_data",
        )
    ):

        if af_packet["protocol"] > 1500:
            out = Packet_802_3(raw_packet)
        else:
            out = Packet_802_2(raw_packet)

        res = packet_filter.apply(af_packet, out)

        if res is None:
            continue
        else:
            feeder.put(res)

    packet_submitter.stop()
    assert True


def test_submitter_useless():

    start_submitter()
