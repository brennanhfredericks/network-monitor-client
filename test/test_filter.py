import queue
import threading
import binascii
import os
import time

from network_monitor.protocols import Packet_802_2, Packet_802_3, AF_Packet
from network_monitor import Packet_Submitter
from network_monitor.filters import present_protocols
from test_load_data import load_filev2


def start_filter():

    assert False


def test_filter():
    start_filter()