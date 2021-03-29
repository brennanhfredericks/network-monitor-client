import struct
import binascii
from dataclasses import dataclass

from .parsers import Protocol_Parser
from .layer import Layer_Protocols

# other LSAP addresses available on https://en.wikipedia.org/wiki/IEEE_802.2

collect_protocols = []  # (level,identifier,parser)


@dataclass
class SNAP_ext(object):
    description = "SNAP extension"
    identifier = 170
    OUI: str
    protocol_id: int

    def __init__(self, raw_bytes):
        __oui, __proto = struct.unpack("! 3s H", raw_bytes[:5])
        self.OUI = binascii.b2a_hex(__oui)
        self.protocol_id = __proto

        self.__raw_bytes = raw_bytes

        self.__parse_upper_layer(raw_bytes[5:])

    def raw(self):
        return self.__raw_bytes

    def upper_layer(self):

        return self.__encap

    def __parse_upper_layer(self, remaining_raw_bytes):
        self.__encap = Protocol_Parser.parse(
            Layer_Protocols.Ethertype, self.protocol_id, remaining_raw_bytes
        )


collect_protocols.append((Layer_Protocols.LSAP_addresses, 170, SNAP_ext))


def get_LLC_layer_parsers():
    return collect_protocols