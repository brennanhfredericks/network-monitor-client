import queue
import threading
import binascii
import os
import time
import sys
import configparser

from network_monitor.protocols import (
    Packet_802_2,
    Packet_802_3,
    AF_Packet,
    TCP,
    IPv4,
    Protocol_Parser,
)
from network_monitor import Packet_Filter, Filter, load_configuration
from network_monitor.filters import present_protocols
from test_load_data import load_filev2, load_submitter_local_log

# increase test coverage for filter implementation
def start_filter():
    packet_filter = Packet_Filter()

    # create Filter to filter all packets send by application to monitor services

    t0_filter = Filter(
        "test0",
        {
            "IPv4": {
                "source_address": "127.0.0.1",
                "destination_address": "127.0.0.1",
            },
            "AF_Packet": {"ifname": "lo"},
        },
    )

    packet_filter.register(t0_filter)

    for i, (af_packet, raw_bytes) in enumerate(
        load_filev2(
            "raw2_protocols_1617213286_IPv4_IPv6_UDP_TCP_ARP_ICMP_ICMPv6_IGMP_LLDP_CDP.lp",
            log_dir="./remote_data",
        )
    ):

        if af_packet["protocol"] > 1500:
            out_packet = Packet_802_3(raw_bytes)
        else:
            out_packet = Packet_802_2(raw_bytes)

        res = packet_filter.apply(af_packet, out_packet)

        if res is None:
            continue
        else:
            ret = []
            for proto_name, proto_attrs in t0_filter.definition.items():
                try:
                    value = res[proto_name]
                except IndexError:
                    ret.append(False)
                else:
                    _ret = []
                    for k, v in proto_attrs.items():
                        _ret.append(value[k] == v)

                    ret.append(all(_ret))

            assert all(ret) == False


def test_filter():
    start_filter()


def configuration_file_filters():
    base_dir = "configuration_output"
    dirs = os.listdir(base_dir)
    config = configparser.ConfigParser()
    for p in dirs:
        p_ = os.path.join(base_dir, p)
        files = [os.path.join(p_, f) for f in os.listdir(p_)]

        conf_fname = files[0] if files[0].endswith(".cfg") else files[1]
        output_fname = files[0] if files[0].endswith(".lsp") else files[1]

        print(conf_fname, output_fname)

        config = load_configuration(conf_fname)
        packet_filter = Packet_Filter()

        res = []
        # load local packets
        for packet in load_submitter_local_log(output_fname):
            # packet
            for filtr in config.Filters:
                res.append(filtr.apply(packet))

    assert any(res) == False


def test_configuration_file_filters():
    configuration_file_filters()