

import os
import binascii
import threading
import queue
import sys

sys.path.insert(0, "./")

from network_monitor.filters import get_protocol  # noqa
from network_monitor.protocols import (  # noqa
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

# Protocol_Parser.set_log_directory("./logs/application/unknown_protocols")
