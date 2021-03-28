import sys

sys.path.insert(0, "../")

import queue
import threading
import binascii
import os

from network_monitor import (
    Service_Manager,
    Interface_Listener,
)

from network_monitor.protocols import AF_Packet, Packet_802_3, TCP, UDP
from network_monitor.filters import get_protocol


def log_ipv4_packets(ifname, number):

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

            if len(raw_packets) == number:
                waitfor = False
    service_manager.stop_all_services()

    if not os.path.exists("./raw_output"):
        os.makedirs("./raw_output")

    # file output name
    outname = f"./raw_output/raw_ipv4_output.lp"

    with open(outname, "wb") as fout:
        for i, packet in enumerate(raw_packets):

            base64 = binascii.b2a_base64(packet)
            fout.write(base64)
    print("finished with IPv4")


def log_ipv6_packets(ifname, number):

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

            if af_packet.proto == 34525:
                raw_packets.append(raw_bytes)

            if len(raw_packets) == number:
                waitfor = False
    service_manager.stop_all_services()

    # file output name
    outname = f"./raw_output/raw_ipv6_output.lp"

    with open(outname, "wb") as fout:
        for i, packet in enumerate(raw_packets):

            base64 = binascii.b2a_base64(packet)
            fout.write(base64)
    print("finished with IPv6")


def log_arp_packets(ifname, number):

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

            if af_packet.proto == 2054:
                raw_packets.append(raw_bytes)

            if len(raw_packets) == number:
                waitfor = False
    service_manager.stop_all_services()

    # file output name
    outname = f"./raw_output/raw_arp_output.lp"

    with open(outname, "wb") as fout:
        for i, packet in enumerate(raw_packets):

            base64 = binascii.b2a_base64(packet)
            fout.write(base64)
    print("finished with ARP")


def log_tcp_packets(ifname, number):

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

            # only in 802_3 packets
            if af_packet.proto > 1500:

                out_packet = Packet_802_3(raw_bytes)

                out = get_protocol(out_packet, TCP)

                if out is not None:

                    raw_packets.append(out.raw())

            if len(raw_packets) == number:
                waitfor = False
    service_manager.stop_all_services()

    # file output name
    outname = f"./raw_output/raw_tcp_output.lp"

    with open(outname, "wb") as fout:
        for i, packet in enumerate(raw_packets):

            base64 = binascii.b2a_base64(packet)
            fout.write(base64)
    print("finished with tcp")


def log_udp_packets(ifname, number):

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

            # only in 802_3 packets
            if af_packet.proto > 1500:

                out_packet = Packet_802_3(raw_bytes)

                out = get_protocol(out_packet, UDP)

                if out is not None:
                    raw_packets.append(out.raw())

            if len(raw_packets) == number:
                waitfor = False
    service_manager.stop_all_services()

    # file output name
    outname = f"./raw_output/raw_udp_output.lp"

    with open(outname, "wb") as fout:
        for i, packet in enumerate(raw_packets):

            base64 = binascii.b2a_base64(packet)
            fout.write(base64)
    print("finished with udp")


# reduce to single function

if __name__ == "__main__":
    # log_ipv4_packets("enp0s3", 100)
    # log_ipv6_packets("enp0s3", 10)
    # log_arp_packets("enp0s3", 10)
    log_tcp_packets("enp0s3", 1000)
    log_udp_packets("enp0s3", 1000)
    # exit(log_packets("enp0s3"))
