import binascii
import struct
import dataclasses
import json

from itertools import zip_longest
from typing import Optional, Any, Iterable, Dict, Union


def get_ipv4_addr(address: bytes) -> str:
    return ".".join(map(str, address))


def get_mac_addr(address: bytes) -> str:
    addr_str = map("{:02x}".format, address)
    return ":".join(addr_str).upper()


def get_ipv6_addr(address: bytes) -> str:
    addr_str = [
        binascii.b2a_hex(x).decode("utf-8")
        for x in struct.unpack("! 2s 2s 2s 2s 2s 2s 2s 2s", address)
    ]
    return ":".join(addr_str)


def grouper(iterable: Iterable, n: int, fillvalue: Optional[str] = None) -> list:
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


@dataclasses.dataclass
class Unknown(object):
    Description = "Unknown Protocol"
    Identifier: -99
    Message: str
    Protocol_Identifier: int

    def __init__(self, message: str, ether_identifier: int, raw_bytes: bytes) -> None:

        self.Message: str = message
        self.Protocol_Identifier: int = ether_identifier
        self.__raw_bytes: bytes = raw_bytes

    def raw(self) -> bytes:

        return self.__raw_bytes

    def upper_layer(self) -> Optional[Any]:

        return None

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)


# https://stackoverflow.com/a/51286749
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o) -> Dict[str, str]:
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)
