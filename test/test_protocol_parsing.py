import sys

sys.path.insert(0, "./")

import queue
import threading
import binascii
import os

from network_monitor.protocols import (
    Packet_802_2,
    Packet_802_3,
    IPv4,
    TCP,
    UDP,
    ARP,
    IPv6,
    ICMP,
    ICMPv6,
    IGMP,
    LLDP,
    Protocol_Parser,
)
from network_monitor.filters import get_protocol
from test_load_data import load_file, load_unknown_file


Protocol_Parser.set_log_directory("./logs/application/unknown_protocols")


def ipv4_packets():
    """ test ipv4 parsing """
    res = []
    for packet in load_file(
        [
            "raw_protocols_1616955106_IPv4_IPv6.lp",
            "raw_protocols_1616954194_TCP_UDP.lp",
            "raw_protocols_1616954194_TCP_UDP.lp",
            "raw_protocols_1616954194_TCP_UDP.lp",
        ],
        log_dir="./test/remote_data",
    ):

        out_packet = Packet_802_3(packet)

        out_proto = get_protocol(out_packet, IPv4)

        if out_proto is None:
            continue

        else:
            res.append(out_proto.identifier == IPv4.identifier)

    return res


def test_ipv4_protocol():

    assert all(ipv4_packets()) == True


def ipv6_packets():
    """ test ipv6 parsing """
    res = []
    for packet in load_file(
        [
            "raw_protocols_1616955106_IPv4_IPv6.lp",
            "raw_protocols_1616954194_TCP_UDP.lp",
            "raw_protocols_1616954194_TCP_UDP.lp",
            "raw_protocols_1616954194_TCP_UDP.lp",
        ],
        log_dir="./test/remote_data",
    ):

        out_packet = Packet_802_3(packet)

        out_proto = get_protocol(out_packet, IPv6)

        if out_proto is None:
            continue

        else:
            res.append(out_proto.identifier == IPv6.identifier)

    return res


def test_ipv6_protocol():

    assert all(ipv6_packets()) == True


def arp_packets():
    """ test arp parsing """
    res = []
    for packet in load_file(
        "raw_protocols_1616955371_ARP_ICMP_ICMPv6_IGMP.lp", log_dir="./test/remote_data"
    ):

        out_packet = Packet_802_3(packet)

        out_proto = get_protocol(out_packet, ARP)

        if out_proto is None:
            continue

        else:
            res.append(out_proto.identifier == ARP.identifier)

    return res


def test_arp_protocol():

    assert all(arp_packets()) == True


def tcp_packets():
    """ test test parsing """
    res = []
    for packet in load_file(
        [
            "raw_protocols_1616954194_TCP_UDP.lp",
            "raw_protocols_1616954635_TCP_UDP.lp",
            "raw_protocols_1616954635_TCP_UDP.lp",
        ],
        log_dir="./test/remote_data",
    ):

        out_packet = Packet_802_3(packet)

        out_proto = get_protocol(out_packet, TCP)

        if out_proto is None:
            continue

        else:
            res.append(out_proto.identifier == TCP.identifier)

    return res


def test_tcp_protocol():

    assert all(tcp_packets()) == True


def udp_packets():
    """ test test parsing """
    res = []
    for packet in load_file(
        [
            "raw_protocols_1616954194_TCP_UDP.lp",
            "raw_protocols_1616954635_TCP_UDP.lp",
            "raw_protocols_1616954635_TCP_UDP.lp",
        ],
        log_dir="./test/remote_data",
    ):

        out_packet = Packet_802_3(packet)

        out_proto = get_protocol(out_packet, UDP)

        if out_proto is None:
            continue

        else:
            res.append(out_proto.identifier == UDP.identifier)

    return res


def test_udp_protocol():

    assert all(udp_packets()) == True


def icmp_packets():
    """ test icmp parsing """
    res = []
    for packet in load_file(
        "raw_protocols_1617059888_ARP_ICMP_ICMPv6_IGMP.lp", log_dir="./test/remote_data"
    ):

        out_packet = Packet_802_3(packet)

        out_proto = get_protocol(out_packet, ICMP)

        if out_proto is None:
            continue

        else:
            res.append(out_proto.identifier == ICMP.identifier)

    return res


def test_icmp_protocol():

    assert all(icmp_packets()) == True


def icmpv6_packets():
    """ test icmpv6 parsing """
    res = []
    for packet in load_file(
        "raw_protocols_1616955371_ARP_ICMP_ICMPv6_IGMP.lp", log_dir="./test/remote_data"
    ):

        out_packet = Packet_802_3(packet)

        out_proto = get_protocol(out_packet, ICMPv6)

        if out_proto is None:
            continue

        else:

            res.append(out_proto.identifier == ICMPv6.identifier)

    return res


def test_icmpv6_protocol():

    assert all(icmpv6_packets()) == True


def igmp_packets():
    """ test igmp parsing """
    res = []
    for packet in load_file(
        "raw_protocols_1616955371_ARP_ICMP_ICMPv6_IGMP.lp", log_dir="./test/remote_data"
    ):

        out_packet = Packet_802_3(packet)

        out_proto = get_protocol(out_packet, IGMP)

        if out_proto is None:
            continue

        else:
            res.append(out_proto.identifier == IGMP.identifier)

    return res


def test_igmp_protocol():

    assert all(igmp_packets()) == True


def unknown_packets():
    """ test unknown parsing """
    res = []
    # load_unknown_file("raw_unknown_protocols_1617059887.lp", log_dir="./remote_data")

    for layer_protocol, identifier, packet in load_unknown_file(
        [
            "raw_unknown_protocols_1616954194.lp",
            "raw_unknown_protocols_1616954635.lp",
            "raw_unknown_protocols_1616954635.lp",
            "raw_unknown_protocols_1616955371.lp",
            "raw_unknown_protocols_1617059887.lp",
        ],
        log_dir="./test/remote_data",
    ):

        out_proto = LLDP(packet)
        res.append(out_proto.identifier == LLDP.identifier)

    return res


def test_unknown_protocol():

    assert all(unknown_packets()) == True


if __name__ == "__main__":

    exit(test_unknown_protocol())