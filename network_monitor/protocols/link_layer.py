import socket
import struct
import sys

import json
import base64
import dataclasses

from dataclasses import dataclass
from .protocol_utils import get_mac_addr, EnhancedJSONEncoder, Unknown
from .layer import Layer_Protocols
from .parsers import Protocol_Parser

from typing import Optional, Dict, Any, Union, Tuple

PKTTYPE_LOOKUP = {
    socket.PACKET_BROADCAST: "PACKET_BROADCAST",
    socket.PACKET_FASTROUTE: "PACKET_FASTROUTE",
    socket.PACKET_HOST: "PACKET_HOST",
    socket.PACKET_MULTICAST: "PACKET_MULTICAST",
    socket.PACKET_OTHERHOST: "PACKET_OTHERHOST",
    socket.PACKET_OUTGOING: "PACKET_OUTGOING",
}


@dataclass
class AF_Packet(object):
    """ Class for parsing low level packets"""

    Interface_Name: str
    Ethernet_Protocol_Number: int
    Packet_Type: str
    ARP_Hardware_Address_Type: int
    Hardware_Physical_Address: str

    def __init__(self, address: Tuple[str, int, int, int, bytes]) -> None:

        self.Interface_Name: str = address[0]
        self.Ethernet_Protocol_Number: int = address[1]
        self.Packet_Type: str = PKTTYPE_LOOKUP[address[2]]
        self.ARP_Hardware_Address_Type: int = address[3]
        self.Hardware_Physical_Address: str = get_mac_addr(address[4])

    def serialize(self) -> Dict[str, Union[str, int]]:

        return dataclasses.asdict(self)


Protocol_Parser._register_protocol_class_name("AF_Packet", AF_Packet)


@dataclass
class Packet_802_2(object):

    Description = "Ethernet 802.2 LLC Packet"
    Identifier = -2
    DSAP: str
    SSAP: str
    Control: str

    def __init__(self, raw_bytes: bytes) -> None:
        # https://en.wikipedia.org/wiki/IEEE_802.2

        # 802.2 LLC PDU
        __dsap, __ssap, __ctl = struct.unpack("! B B B", raw_bytes[:3])
        self.DSAP: str = __dsap
        self.SSAP: str = __ssap

        # check if control field is 8 bit or 16 bit
        if __ctl & 3 == 3:
            self.Control: str = __ctl
            self.__parse_upper_layer_protocol(raw_bytes[3:])
        else:
            _, _, __ctl = struct.unpack("! B B H", raw_bytes[:4])
            self.Control: str = __ctl
            self.__parse_upper_layer_protocol(raw_bytes[4:])
        self._LSAP_info: Dict[str, str] = {}

        # DSAP
        if self.DSAP & 1 == 0:
            # if lower-order bit is 0 - individual address
            # there are mulitple individual LSAP addresses

            self._LSAP_info["DSAP"] = "individual address"
        else:
            # if lower-order bit is 1 - group address
            self._LSAP_info["DSAP"] = "group address"

        # SSAP
        if self.SSAP & 1 == 0:
            # if lower-order bit is 0 - command packet
            self._LSAP_info["SSAP"] = "command"
        else:
            # if lower-order bit is 1 - response packet
            self._LSAP_info["SSAP"] = "response"

        # store raw
        self._raw_bytes: bytes = raw_bytes

    def raw(self) -> bytes:
        return self._raw_bytes

    def upper_layer(self) -> Any:

        return self.__encap

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)

    def __parse_upper_layer_protocol(self, remaining_raw_bytes) -> None:

        self.__encap: Any = Protocol_Parser.parse(
            Layer_Protocols.LSAP_addresses, self.DSAP, remaining_raw_bytes
        )


Protocol_Parser._register_protocol_class_name("Packet_802_2", Packet_802_2)


@dataclass
class Packet_802_3(object):
    Description = "Ethernet 802.3 Packet"
    Identifier = -3
    Destination_MAC: str
    Source_MAC: str
    Ethertype: int

    def __init__(self, raw_bytes: bytes) -> None:
        __des_addr, __src_addr, __tp = struct.unpack(
            "! 6s 6s H", raw_bytes[:14])
        self.Destination_MAC: str = get_mac_addr(__des_addr)
        self.Source_MAC: str = get_mac_addr(__src_addr)
        self.Ethertype: int = __tp

        self._raw_bytes: bytes = raw_bytes

        self.__parse_upper_layer_protocol(raw_bytes[14:])

    def raw(self) -> bytes:
        return self._raw_bytes

    def upper_layer(self) -> Any:
        return self.__encap

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)

    def __parse_upper_layer_protocol(self, remaining_raw_bytes: bytes) -> Any:
        self.__encap: Any = Protocol_Parser.parse(
            Layer_Protocols.Ethertype, self.Ethertype, remaining_raw_bytes
        )


Protocol_Parser._register_protocol_class_name("Packet_802_3", Packet_802_3)

# add here to avoid cicular reference link layer protocol to protocol lookup table
Protocol_Parser._register_protocol_class_name("Unknown", Unknown)
