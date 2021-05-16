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


#Protocol_Parser.set_log_directory("./logs/application/unknown_protocols")


