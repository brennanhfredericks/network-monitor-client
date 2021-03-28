import sys

sys.path.insert(0, "../")

import queue
import threading
import binascii
import os
import time
import signal

from network_monitor import (
    Service_Manager,
    Interface_Listener,
)

from network_monitor.protocols import (
    AF_Packet,
    Packet_802_3,
    TCP,
    UDP,
    IGMP,
    ICMP,
    ICMPv6,
    IPv4,
    IPv6,
    ARP,
)
from network_monitor.filters import get_protocol, present_protocols


def log_packets_based_on_protocols(
    ifname: str, proto_list: list, min_number: int = 5, max_number: int = 10
):
    start_time = int(time.time())
    service_manager = Service_Manager(ifname)
    input_queue = queue.Queue()
    # output_queue = queue.Queue()

    # start network listener
    interface_listener = Interface_Listener(ifname, input_queue)
    service_manager.start_service("interface listener", interface_listener)

    raw_packets = []

    def create_name() -> str:
        """
        create name for file
        raw_protocols_1548866456123_15484646453212_ARP_IPv4_IPv6_ICMP.lp"""
        fname = f"raw_protocols_{start_time}_{int(time.time())}_"

        for proto_cls in proto_list:
            print(proto_cls.__name__)

    def log_to_disk():
        """write raw_packets to disk and exit"""
        # create_name()

    # exit cleanly
    def signal_handler(sig, frame):
        # log_to_disk()
        service_manager.stop_all_services()
        sys.exit(0)

    # signal.signal(signal.SIGTSTP, signal_handler)
    # signal.signal(signal.SIGINT, signal_handler)

    waitfor = True

    while waitfor:

        if not input_queue.empty():
            print("got packet")
            raw_bytes, address = input_queue.get()

            af_packet = AF_Packet(address)

            if af_packet.proto > 1500:
                out_packet = Packet_802_3(raw_bytes)

                present_protos = present_protocols(out_packet)
                print(present_protos)
                waitfor = False

    service_manager.stop_all_services()


if __name__ == "__main__":

    log_packets_based_on_protocols("enp0s3", [IPv4, ARP, IPv6])
