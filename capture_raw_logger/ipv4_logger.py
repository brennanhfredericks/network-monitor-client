import sys

sys.path.insert(0, "../")

import queue
import threading
import binascii

from network_monitor import (
    Service_Manager,
    Packet_Parser,
    Interface_Listener,
    AF_Packet,
)


def log_packets(ifname):

    service_manager = Service_Manager(ifname)
    input_queue = queue.Queue()
    output_queue = queue.Queue()

    # start network listener
    interface_listener = Interface_Listener(ifname, input_queue)
    service_manager.start_service("interface listener", interface_listener)
    raw_packets = []
    waitfor = True
    while waitfor:

        if not input_queue.empty():

            raw_bytes, address = input_queue.get()

            af_packet = AF_Packet(address)

            if af_packet.proto == 2048:
                raw_packets.append(raw_bytes)

            if len(raw_packets) == 10:
                waitfor = False
    service_manager.stop_all_services()

    # file output name
    outname = f"./raw_output/raw_ipv4_output.lp"

    with open(outname, "wb") as fout:
        for i, packet in enumerate(raw_packets):

            base64 = binascii.b2a_base64(packet)
            fout.write(base64)


if __name__ == "__main__":

    exit(log_packets("enp0s3"))