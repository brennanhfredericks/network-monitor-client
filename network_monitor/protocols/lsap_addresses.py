import struct
import base64
import sys
import dataclasses
from dataclasses import dataclass
from typing import Optional, Any, Dict, Union
from .parsers import Protocol_Parser
from .layer import Layer_Protocols

# other LSAP addresses available on https://en.wikipedia.org/wiki/IEEE_802.2


@dataclass
class LSAP_One(object):
    Description = "my_identifeier_not_sure"
    Identifier = 1
    Message: str

    def __init__(self, raw_bytes: bytes) -> None:
        (__msg,) = struct.unpack(f"! {len(raw_bytes)}s", raw_bytes)

        self.Message: str = base64.b64encode(__msg).decode("utf-8")
        self._raw_bytes: bytes = raw_bytes

    def raw(self) -> bytes:
        return self._raw_bytes

    def upper_layer(self) -> Optional[Any]:
        return None

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)


Protocol_Parser.register(Layer_Protocols.LSAP_addresses, 1, LSAP_One)


@dataclass
class SNAP_Ext(object):
    Description = "SNAP extension"
    Identifier = 170
    OUI: str
    Protocol_ID: int

    def __init__(self, raw_bytes: bytes) -> None:
        __oui, __proto = struct.unpack("! 3s H", raw_bytes[:5])
        self.OUI = int.from_bytes(__oui, sys.byteorder)
        self.Protocol_ID = __proto

        self.__raw_bytes: bytes = raw_bytes

        self.__parse_upper_layer(raw_bytes[5:])

    def raw(self) -> bytes:
        return self.__raw_bytes

    def upper_layer(self) -> Optional[Any]:

        return self.__encap

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)

    def __parse_upper_layer(self, remaining_raw_bytes: bytes):

        if self.OUI == 0:
            self.__encap = Protocol_Parser.parse(
                Layer_Protocols.Ethertype, self.Protocol_ID, remaining_raw_bytes
            )
        else:
            # if the OUI is an OUI for a particular organization, the protocol ID is
            # a value assigned by that organization to the protocol running on top
            # of SNAP.

            self.__encap = remaining_raw_bytes


Protocol_Parser.register(Layer_Protocols.LSAP_addresses, 170, SNAP_Ext)
