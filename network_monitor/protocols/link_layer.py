import socket
import struct
import sys

import json
import base64

from dataclasses import dataclass
from .protocol_utils import get_mac_addr, EnhancedJSONEncoder
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

    def serialize_to_bytes(self):
        ret = {
            "ifname": self.ifname,
            "proto": self.proto,
            "pkttype": self.pkttype,
            "hatype": self.hatype,
            "hwadddr": self.hwaddr,
        }
        ret = base64.b64encode(json.dumps(ret).encode("utf-8"))

        return ret

    def serialize(self):
        ret = {
            "ifname": self.ifname,
            "proto": self.proto,
            "pkttype": self.pkttype,
            "hatype": self.hatype,
            "hwadddr": self.hwaddr,
        }
        ret = base64.b64encode(json.dumps(ret).encode("utf-8")).decode("utf-8")

        return ret


@dataclass
class Packet_802_2(object):

    description = "Ethernet 802.2 LLC Packet"
    identifier = -2
    DSAP: str
    SSAP: str
    control: str

    def __init__(self, raw_bytes):
        # https://en.wikipedia.org/wiki/IEEE_802.2

        # 802.2 LLC PDU
        __dsap, __ssap, __ctl = struct.unpack("! B B B", raw_bytes[:3])
        self.DSAP = __dsap
        self.SSAP = __ssap

        # check if control field is 8 bit or 16 bit
        if __ctl & 3 == 3:
            self.control = __ctl
            self.__parse_upper_layer_protocol(raw_bytes[3:])
        else:
            __ctl = struct.unpack("! x x H", raw_bytes[:4])
            self.control = __ctl
            self.__parse_upper_layer_protocol(raw_bytes[4:])
        self._LSAP_info = {}

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
        self._raw_bytes = raw_bytes

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):

        return self.__encap

    def serialize(self):
        return json.dumps(self, cls=EnhancedJSONEncoder)

    def __parse_upper_layer_protocol(self, remaining_raw_bytes):

        self.__encap = Protocol_Parser.parse(
            Layer_Protocols.LSAP_addresses, self.DSAP, remaining_raw_bytes
        )


@dataclass
class Packet_802_3(object):
    description = "Ethernet 802.3 Packet"
    identifier = -3
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

    def serialize(self):
        return json.dumps(self, cls=EnhancedJSONEncoder)

    def __parse_upper_layer_protocol(self, remaining_raw_bytes):
        self.__encap = Protocol_Parser.parse(
            Layer_Protocols.Ethertype, self.ethertype, remaining_raw_bytes
        )


# manual hack to add link layer protocol to protocol lookup table

Protocol_Parser._register_protocol_class_name("AF_Packet", AF_Packet)
Protocol_Parser._register_protocol_class_name("Packet_802_3", Packet_802_3)
Protocol_Parser._register_protocol_class_name("Packet_802_2", Packet_802_2)
