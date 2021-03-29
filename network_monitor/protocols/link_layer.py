import socket
import struct
import sys
import binascii

from dataclasses import dataclass
from .protocol_utils import get_mac_addr
from .layer import Layer_Protocols
from .parsers import Protocol_Parser

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

    ifname: str
    proto: int
    pkttype: str
    hatype: int
    hwaddr: str

    def __init__(self, address):

        self.ifname = address[0]
        self.proto = address[1]
        self.pkttype = PKTTYPE_LOOKUP[address[2]]
        self.hatype = address[3]
        self.hwaddr = get_mac_addr(address[4])


@dataclass
class Packet_802_2(object):

    description = "Ethernet 802.2 LLC Packet"
    DSAP: str
    SSAP: str
    control: str
    OUI: str
    protocol_id: int

    def __init__(self, raw_bytes):

        # could be unpacking this wrong need to verify
        # __dsap, __ssap, __ctl, __oi, __code = struct.unpack(
        #     "! c c c 3s H", raw_bytes[:8]
        # )

        # alternative unpacking
        __dsap, __ssap, __ctl, __oui, __code = struct.unpack(
            "! c c 2s 3s H", raw_bytes[:9]
        )

        # 802.2 LLC Header
        self.DSAP = binascii.b2a_hex(__dsap)
        self.SSAP = binascii.b2a_hex(__ssap)
        self.control = binascii.b2a_hex(__ctl)

        # SNAP extension
        self.OUI = binascii.b2a_hex(__oui)
        self.protocol_id = __code

        # store raw
        self._raw_bytes = raw_bytes

        self.__parse_upper_layer_protocol(raw_bytes[9:])

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):
        raise NotImplemented

    def __parse_upper_layer_protocol(self, remaining_raw_bytes):
        # not parser out, need to investigate futher
        self.__encap = remaining_raw_bytes


@dataclass
class Packet_802_3(object):
    description = "Ethernet 802.3 Packet"
    dest_MAC: str
    src_MAC: str
    ethertype: int

    def __init__(self, raw_bytes):
        __des_addr, __src_addr, __tp = struct.unpack("! 6s 6s H", raw_bytes[:14])
        self.dest_MAC = get_mac_addr(__des_addr)
        self.src_MAC = get_mac_addr(__src_addr)
        self.ethertype = __tp

        self._raw_bytes = raw_bytes

        self.__parse_upper_layer_protocol(raw_bytes[14:])

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):
        return self.__encap

    def __parse_upper_layer_protocol(self, remaining_raw_bytes):
        # hack for 802 test
        if self.ethertype == 103:
            print(Packet_802_2(remaining_raw_bytes))
        self.__encap = Protocol_Parser.parse(
            Layer_Protocols.Ethertype, self.ethertype, remaining_raw_bytes
        )
