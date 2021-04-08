import binascii
import struct
from itertools import zip_longest
import dataclasses
import json


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


# from https://stackoverflow.com/questions/3949726/calculate-ip-checksum-in-python
# def carry_around_add(a, b):
#     c = a + b
#     return (c & 0xFFFF) + (c >> 16)


# def verify_checksum(msg):
#     s = 0
#     for i in range(0, len(msg), 2):
#         w = ord(msg[i]) + (ord(msg[i + 1]) << 8)
#         s = carry_around_add(s, w)
#     return ~s & 0xFFFF

# https://stackoverflow.com/questions/29842280/python16-bit-ones-complement-addition-implementation
MOD = 1 << 16


def ones_comp_add16(num1, num2):
    result = num1 + num2
    return result if result < MOD else (result + 1) % MOD


@dataclasses.dataclass
class Unknown(object):
    description = "Unknown Protocol"
    message: str
    identifier: -99

    def __init__(self, message: str, identifier: int, raw_bytes: bytes):

        self.message = message
        self.identifier = identifier
        self.__raw_bytes = raw_bytes

    def raw(self):

        return self.__raw_bytes

    def upper_layer(self):

        return None

    def serialize(self):
        return dataclasses.asdict(self)


# https://stackoverflow.com/a/51286749
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)
