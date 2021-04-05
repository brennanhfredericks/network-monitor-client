import sys

sys.path.insert(0, "../")

import queue
import threading
import binascii
import os
import time

from network_monitor.protocols import Packet_802_2, Packet_802_3, AF_Packet
from network_monitor import Packet_Submitter
from network_monitor.filters import present_protocols
from test_load_data import load_filev2


def start_submitter():

    feeder = queue.Queue()

    packet_submitter = Packet_Submitter(feeder)

    packet_submitter.start()
    for i, (af_packet, packet) in enumerate(
        load_filev2(
            "raw2_protocols_1617213286_IPv4_IPv6_UDP_TCP_ARP_ICMP_ICMPv6_IGMP_LLDP_CDP.lp",
            log_dir="./remote_data",
        )
    ):

        if af_packet["protocol"] > 1500:
            out = Packet_802_3(packet)
        else:
            out = Packet_802_2(packet)
        # out_protos = present_protocols(out)

        feeder.put((af_packet, out))

        if i % 20 == 0 and i != 0:
            time.sleep(0.5)
            # break
    packet_submitter.stop()
    assert False


def test_submitter():

    start_submitter()