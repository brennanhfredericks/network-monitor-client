import sys

sys.path.insert(0, "../")

import queue
import threading
import base64

import os
import time
import signal
import collections

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
    LLDP,
    CDP,
)
from network_monitor.filters import get_protocol, present_protocols

# write to tmp file and replace with os.replace
def log_packets_based_on_protocols(
    ifname: str,
    proto_list: list,
    min_number: int = 5,
    log_dir="./logger_output",
    report_interval: int = 5,
    log_802_2=True,
):
    start_time = int(time.time())
    service_manager = Service_Manager(ifname)
    input_queue = queue.Queue()
    # output_queue = queue.Queue()

    # start network listener
    interface_listener = Interface_Listener(ifname, input_queue)
    service_manager.start_service("interface listener", interface_listener)

    tracker = collections.Counter({proto.identifier: 0 for proto in proto_list})

    def create_name() -> str:
        """
        create name for file
        raw_protocols_1548866456123_ARP_IPv4_IPv6_ICMP.lp"""

        fname = f"raw2_protocols_{start_time}"

        for proto_cls in proto_list:
            fname += f"_{proto_cls.__name__}"

        fname += ".lp"

        return fname

    # exit cleanly
    def signal_handler(sig, frame):
        # log_to_disk()
        service_manager.stop_all_services()
        sys.exit(0)

    signal.signal(signal.SIGTSTP, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    fname = create_name()

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    waitfor = True
    last_report_time = time.time()
    with open(os.path.join(log_dir, fname), "wb") as fout:
        while waitfor:

            if not input_queue.empty():

                raw_bytes, address = input_queue.get()

                af_packet = AF_Packet(address)
                fout.write(af_packet.serialize_to_bytes())
                if af_packet.proto > 1500:
                    out_packet = Packet_802_3(raw_bytes)
                    write_packet = False
                    for identifier in present_protocols(out_packet):
                        if identifier in tracker.keys():
                            tracker[identifier] += 1
                            write_packet = True

                    if write_packet:

                        __tracker = {k: v for k, v in tracker.items()}
                        fout.write(base64.b64encode(raw_bytes))
                        fout.write(b"\n")
                        now = time.time()
                        if now - last_report_time > report_interval:
                            last_report_time = now

                            print(f"Tracker: {__tracker}")
                else:

                    if log_802_2:
                        # log in a seperate file to avoid hack for testing purposes
                        fout.write(base64.b64encode(raw_bytes))

                if all(map(lambda x: x >= min_number, tracker.values())):
                    waitfor = False

    service_manager.stop_all_services()


if __name__ == "__main__":

    # log_packets_based_on_protocols("br0", [TCP, UDP], min_number=100)
    # log_packets_based_on_protocols("br0", [IPv4, IPv6], min_number=100)
    log_packets_based_on_protocols(
        "enp0s3",
        [IPv4, IPv6, UDP, TCP, ARP, ICMP, ICMPv6, IGMP, LLDP, CDP],
        min_number=10,
    )
