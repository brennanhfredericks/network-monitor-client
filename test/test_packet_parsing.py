import sys

sys.path.insert(0, "../")

import queue
import threading
import binascii
import os

from network_monitor.protocols import Packet_802_3, IPv4, TCP, UDP

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


def packet_layer_walk(out_packet, cls):

    if out_packet is None:
        return None
    elif isinstance(out_packet, cls):
        return out_packet
    else:
        out = packet_layer_walk(out_packet.upper_layer(), cls)

    return out


def gen_packet():
    ret = []
    for packet in load_file("raw_ipv4_output.lp"):
        out_packet = Packet_802_3(packet)
        res_walk = packet_layer_walk(out_packet, IPv4)

        # implement if here to save certain packets

        print(res_walk)

        ret.append(out_packet.ethertype == res_walk.identifier)
        break

    return ret


def test_packet_layer_walk():

    assert all(gen_packet()) == True
