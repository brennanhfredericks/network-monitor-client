import sys

sys.path.insert(0, "../")

import queue
import threading
import binascii
import os

from network_monitor.protocols import (
    Packet_802_3,
    IPv4,
    TCP,
    UDP,
    ARP,
    IPv6,
    Packet_802_2,
)
from network_monitor.filters import get_protocol
from test_load_data import load_file, load_filev2

# content of
def ipv4_packets():
    ret = []
    for packet in load_file("raw_ipv4_output.lp"):
        out_packet = Packet_802_3(packet)
        out = get_protocol(out_packet, IPv4)

        ret.append(out.identifier == IPv4.identifier)
        ret.append(out_packet.ethertype == IPv4.identifier)

    for packet in load_file(("raw_ipv6_output.lp", "raw_arp_output.lp")):
        out_packet = Packet_802_3(packet)

        ret.append(out_packet.ethertype != IPv4.identifier)

    return ret


def test_ipv4_packets():

    assert all(ipv4_packets()) == True


def ipv6_packets():
    ret = []
    for packet in load_file("raw_ipv6_output.lp"):
        out_packet = Packet_802_3(packet)

        ret.append(out_packet.ethertype == IPv6.identifier)

    for packet in load_file(["raw_ipv4_output.lp", "raw_arp_output.lp"]):
        out_packet = Packet_802_3(packet)

        ret.append(out_packet.ethertype != IPv6.identifier)

    return ret


def test_ipv6_packets():
    assert all(ipv6_packets()) == True


def arp_packets():
    ret = []
    for packet in load_file("raw_arp_output.lp"):
        out_packet = Packet_802_3(packet)

        ret.append(out_packet.ethertype == ARP.identifier)

    for packet in load_file(["raw_ipv4_output.lp", "raw_ipv6_output.lp"]):
        out_packet = Packet_802_3(packet)

        ret.append(out_packet.ethertype != ARP.identifier)

    return ret


def test_arp_packets():
    assert all(arp_packets()) == True


def gen_packet():
    ret = []
    for packet in load_file("raw_ipv4_output.lp"):
        out_packet = Packet_802_3(packet)
        res_walk = get_protocol(out_packet, IPv4)

        # implement if here to save certain packets

        ret.append(out_packet.ethertype == res_walk.identifier)

    for packet in load_file("raw_arp_output.lp"):
        out_packet = Packet_802_3(packet)
        res_walk = get_protocol(out_packet, ARP)

        # implement if here to save certain packets

        ret.append(out_packet.ethertype == res_walk.identifier)

    for packet in load_file("raw_ipv6_output.lp"):
        out_packet = Packet_802_3(packet)
        res_walk = get_protocol(out_packet, IPv6)

        # implement if here to save certain packets

        ret.append(out_packet.ethertype == res_walk.identifier)

    return ret


def test_get_protocol():

    assert all(gen_packet()) == True


def tcp_packets():
    ret = []
    for packet in load_file("raw_tcp_output.lp"):
        out_packet = TCP(packet)
        ret.append(out_packet.identifier == TCP.identifier)

    return ret


def test_tcp_packets():
    assert all(tcp_packets()) == True


def udp_packets():
    ret = []
    for packet in load_file("raw_udp_output.lp"):
        out_packet = UDP(packet)
        print(out_packet)
        ret.append(out_packet.identifier == UDP.identifier)

    return ret


def test_udp_packets():
    assert all(udp_packets()) == True


def any_packets():

    ret = []

    for af_packet, packet in load_filev2(
        "raw2_protocols_1617197402_IPv4_IPv6_UDP_TCP_ARP_ICMP_ICMPv6_IGMP_LLDP_CDP.lp",
        log_dir="./remote_data",
    ):
        print(len(packet))
        if af_packet["protocol"] > 1500:
            out = Packet_802_3(packet)
        else:
            out = Packet_802_2(packet)

        print(out)
        break


def test_any_packet():
    any_packets()
    assert False
