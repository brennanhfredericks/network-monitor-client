import struct
import base64
import sys
import dataclasses
from dataclasses import dataclass

from .parsers import Protocol_Parser
from .layer import Layer_Protocols

# other LSAP addresses available on https://en.wikipedia.org/wiki/IEEE_802.2


@dataclass
class LSAP_one(object):
    description = "my_identifeier_not_sure"
    identifier = 1
    message: str

    def __init__(self, raw_bytes):
        (__msg,) = struct.unpack(f"! {len(raw_bytes)}s", raw_bytes)

        self.message = base64.b64encode(__msg).decode("utf-8")
        self._raw_bytes = raw_bytes

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):
        return None

    def serialize(self):
        return dataclasses.asdict(self)


Protocol_Parser.register(Layer_Protocols.LSAP_addresses, 1, LSAP_one)


@dataclass
class SNAP_ext(object):
    description = "SNAP extension"
    identifier = 170
    OUI: str
    protocol_id: int

    def __init__(self, raw_bytes):
        __oui, __proto = struct.unpack("! 3s H", raw_bytes[:5])
        self.OUI = int.from_bytes(_oui, sys.byteorder)
        self.protocol_id = __proto

        self.__raw_bytes = raw_bytes

        self.__parse_upper_layer(raw_bytes[5:])

    def raw(self):
        return self.__raw_bytes

    def upper_layer(self):

        return self.__encap

    def serialize(self):
        return dataclasses.asdict(self)

    def __parse_upper_layer(self, remaining_raw_bytes):

        if self.OUI == 0:
            self.__encap = Protocol_Parser.parse(
                Layer_Protocols.Ethertype, self.protocol_id, remaining_raw_bytes
            )
        else:
            # if the OUI is an OUI for a particular organization, the protocol ID is
            # a value assigned by that organization to the protocol running on top
            # of SNAP.

            self.__encap = remaining_raw_bytes


Protocol_Parser.register(Layer_Protocols.LSAP_addresses, 170, SNAP_ext)
