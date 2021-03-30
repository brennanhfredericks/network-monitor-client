import binascii
import struct
from itertools import zip_longest
from dataclasses import dataclass


def get_ipv4_addr(addr):
    return ".".join(map(str, addr))


def get_mac_addr(addr):
    addr_str = map("{:02x}".format, addr)
    return ":".join(addr_str).upper()


def get_ipv6_addr(addr):
    addr_str = [
        binascii.b2a_hex(x).decode("utf-8")
        for x in struct.unpack("! 2s 2s 2s 2s 2s 2s 2s 2s", addr)
    ]
    return ":".join(addr_str)


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


@dataclass
class Unknown(object):
    description = "Unknown Protocol"
    message: str
    identifier: int

    def __init__(self, message: str, identifier: int, raw_bytes: bytes):

        self.message = message
        self.identifier = identifier
        self.__raw_bytes = raw_bytes

    def raw(self):

        return self.__raw_bytes

    def upper_layer(self):

        return None
