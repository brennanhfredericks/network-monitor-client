import sys
import struct
from dataclasses import dataclass

from .transport_layer import IP_Protocols
from .extension_headers import IPv6_Ext_Headers
from .protocol_utils import get_ipv4_addr, get_ipv6_addr


@dataclass
class IPv4(object):

    description = "Internet Protocol Version 4"
    version: int
    IHL: int
    DSCP: int
    ECN: int
    total_length: int
    identification: int
    flags = int
    fragment_offset: int
    TTL: int
    protocol: int
    header_checksum: int
    source_address: str
    destination_address: str
    options: int = 0

    def __init__(self, raw_bytes):

        (
            __vihl,
            __dsen,
            __tl,
            __ident,
            __ff,
            __ttl,
            __proto,
            __hck,
            __src,
            __des,
        ) = struct.unpack("! B B H H H B B H 4s 4s", raw_bytes[:20])

        __flags = __ff & 57344 >> 13
        self.version = __vihl >> 4

        self.IHL = __vihl & 15
        self.DSCP = (__dsen & 252) >> 2
        self.ECN = __dsen & 3
        self.total_length = __tl
        self.identification = __ident

        self.flags = __flags
        self.fragment_offset = __ff & 8191
        self.TTL = __ttl
        self.protocol = __proto
        self.header_checksum = __hck
        self.source_address = get_ipv4_addr(__src)
        self.destination_address = get_ipv4_addr(__des)

        # Note: If the header length is greater than 5 (i.e., it is from 6 to 15)
        # it means that the options field is present and must be considered.
        if self.IHL > 5:
            # raw bytes contains Option field data
            pass
        else:
            self.__parser_upper_layer_protocol(raw_bytes[20:])

    def _options(self, remaining_raw_bytes):
        """ used to parser Options flield """
        # Note: Copied, Option Class, and Option Number are sometimes referred to as a single eight-bit field, the Option Type.

        # The packet payload is not included in the checksum
        print(f"Options field size: {len(remaining_raw_bytes)}")

    def __parser_upper_layer_protocol(self, remaining_raw_bytes):

        self._encap = IP_Protocols(self.protocol, remaining_raw_bytes)


@dataclass
class IPv6(object):

    description = "Internet Protocol Version 6"
    version: int
    traffic_class: int
    flow_label: int
    payload_length: int
    next_header: int
    hop_limit: int
    source_address: str
    destination_address: str
    ext_headers: list

    def __init__(self, raw_bytes):

        # parse fixed header
        __vtf, __pl_len, __next_h, __hop_l, __src_addr, __des_addr = struct.unpack(
            "! 4s H B B 16s 16s", raw_bytes[:40]
        )

        # index first byte
        self.version = __vtf[0] >> 4
        self.traffic_class = (int.from_bytes(__vtf[:2], sys.byteorder) & 2040) >> 4
        self.flow_label = int.from_bytes(__vtf[1:4], sys.byteorder) & 1048575
        self.payload_length = __pl_len
        self.next_header = __next_h
        self.hop_limit = __hop_l
        self.source_address = get_ipv6_addr(__src_addr)
        self.destination_address = get_ipv6_addr(__des_addr)

        # parse extension headers
        (
            self.ext_headers,
            protocol,
            remaining_raw_bytes,
        ) = IPv6_Ext_Headers().parse_extension_headers(self.next_header, raw_bytes[40:])

        # parse upper layer protocol
        self.__parser_upper_layer_protocol(protocol, remaining_raw_bytes)

    def __parser_upper_layer_protocol(self, protocol, remaining_raw_bytes):
        # The values are shared with those used for the IPv4 protocol field
        self._encap = IPv4_Protocols(protocol, remaining_raw_bytes)


@dataclass
class ARP(object):
    description = "Address Resolution Protocol"

    HTYPE: int
    PTYPE: int
    HLEN: int
    PLEN: int
    operation: int
    SHA: str
    SPA: str
    THA: str
    TPA: str

    def __init__(self, raw_bytes):
        (
            __hardware_type,
            __protocol_type,
            __hlen,
            __plen,
            __op_code,
            __sender_hw_addr,
            __sender_proto_addr,
            __target_hw_addr,
            __target_proto_addr,
        ) = struct.unpack("! H H B B H 6s 4s 6s 4s", raw_bytes[:28])

        self.HTYPE = __hardware_type
        self.PTYPE = __protocol_type
        self.HLEN = __hlen
        self.PLEN = __plen
        self.operation = __op_code
        self.SHA = get_mac_addr(__sender_hw_addr)
        self.SPA = self._decode_protocol_addr(__sender_proto_addr)
        self.THA = get_mac_addr(__target_hw_addr)
        self.TPA = self._decode_protocol_addr(__target_proto_addr)

    def _decode_protocol_addr(self, proto_addr):

        if self.PTYPE == 2048:
            return get_ipv4_addr(proto_addr)
        elif self.PTYPE == 34525:
            return get_ipv6_addr(proto_addr)
        else:
            # add logging functionality here
            print(
                f" address ARP decoding not implemented for {self.PTYPE}, address {proto_addr}"
            )
            return str(proto_addr)


class Ethertype(object):
    """wrapper for the different ethertype parsers

    parser implemented:
        - IPv4
        - ARP
        - IPv6
        - CDP
    """

    ETHERTYPE_LOOKUP = {
        2048: IPv4,
        2054: ARP,
        34525: IPv6,
    }

    def __init__(self, ethertype, raw_bytes):

        try:
            self._encap = self.ETHERTYPE_LOOKUP[ethertype](raw_bytes)
            print(self._encap)
        except KeyError:
            # parser not implemented
            # add logging functionality here

            self._encap = Unknown(f"Parser for Ethertype {ethertype} not implemented")
            print(f"Parser for Ethertype {ethertype} not implemented")

        # would any other exception occur?
