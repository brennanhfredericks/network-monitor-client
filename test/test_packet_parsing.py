import sys

sys.path.insert(0, "../")

import queue
import threading
import binascii
import os

from network_monitor import Packet_802_3

from test_load_data import load_file

# content of
def ipv4_packets():
    ret = []
    for packet in load_file("raw_ipv4_output.lp"):
        out_packet = Packet_802_3(packet)

        ret.append(out_packet.ethertype == 2048)

    for packet in load_file(("raw_ipv6_output.lp", "raw_arp_output.lp")):
        out_packet = Packet_802_3(packet)

        ret.append(out_packet.ethertype != 2048)

    return ret


def test_ipv4_packets():

    assert all(ipv4_packets()) == True


def ipv6_packets():
    ret = []
    for packet in load_file("raw_ipv6_output.lp"):
        out_packet = Packet_802_3(packet)

        ret.append(out_packet.ethertype == 34525)

    for packet in load_file(["raw_ipv4_output.lp", "raw_arp_output.lp"]):
        out_packet = Packet_802_3(packet)

        ret.append(out_packet.ethertype != 34525)

    return ret


def test_ipv6_packets():
    assert all(ipv6_packets()) == True


def arp_packets():
    ret = []
    for packet in load_file("raw_arp_output.lp"):
        out_packet = Packet_802_3(packet)

        ret.append(out_packet.ethertype == 2054)

    for packet in load_file(["raw_ipv4_output.lp", "raw_ipv6_output.lp"]):
        out_packet = Packet_802_3(packet)

        ret.append(out_packet.ethertype != 2054)

    return ret


def test_arp_packets():
    assert all(arp_packets()) == True
