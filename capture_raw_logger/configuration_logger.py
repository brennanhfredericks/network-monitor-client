import sys

sys.path.insert(0, "../")

import queue
import threading
import base64
import binascii
import os
import time
import signal
import collections
import configparser
import json

from network_monitor import (
    Service_Manager,
    Interface_Listener,
    start_from_configuration_file,
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


if __name__ == "__main__":

    """
    Purpose:
        - log ouput of submitter service and configuration file used for testing purposes
    """
    log_dir = "./configuration_output/"
    sample = f"{int(time.time())}"

    out_path = os.path.join(log_dir, sample)

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    # define config file here
    config = configparser.ConfigParser()

    # listener service paramaters
    config.add_section("ListenerService")
    config["ListenerService"]["InterfaceName"] = "enp0s3"

    # submitter service paramters
    config.add_section("SubmitterService")
    config["SubmitterService"]["Local"] = out_path

    # filter paramaters
    config.add_section("Filter")
    config["Filter"]["Definition"] = json.dumps(
        {
            "AF_Packet": {"ifname": "lo"},
        }
    )

    config_path = os.path.join(out_path, "test_filter_config.cfg")
    with open(config_path, "w") as fout:
        config.write(fout)

    start_from_configuration_file(
        config_path, interrupt=True, interrupt_interval=60 * 5
    )
