import sys
import struct
import base64
import json
import dataclasses
from dataclasses import dataclass


from .protocol_utils import (
    get_ipv4_addr,
    get_ipv6_addr,
    get_mac_addr,
    grouper,
    ones_comp_add16,
    EnhancedJSONEncoder,
)

from .parsers import Protocol_Parser
from .layer import Layer_Protocols


collect_protocols = []  # (level,identifier,parser)


@dataclass
class IPv4(object):

    description = "Internet Protocol Version 4"
    identifier = 2048
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
        self.__verify_checksum(raw_bytes[: self.IHL * 4])
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
            offset = 5 * self.IHL  # 8*4 24 bytes
            options = raw_bytes[20:offset]

            self.__parse_options(options)
            self.__parse_upper_layer_protocol(raw_bytes[offset:])
        else:
            self.__parse_upper_layer_protocol(raw_bytes[20:])
            self.options = {}

        self.__raw_bytes = raw_bytes

    def __verify_checksum(self, raw_bytes_header: bytes):
        """ verify checksum is correct """

        # https://www.thegeekstuff.com/2012/05/ip-header-checksum/
        checksum = 0
        read_checksum = 0
        int16s = []
        (raw_bytes_header,) = struct.unpack(
            f"! {len(raw_bytes_header)}s", raw_bytes_header
        )
        for i, (high, low) in enumerate(grouper(raw_bytes_header, 2, fillvalue=0)):

            if i == 5:
                read_checksum = own = f"{(high << 8)+low:x}"
                read_checksum = int(read_checksum, 16)

                int16s.append(0)
                # print(f"0x{int16:04x} ", end="")

            else:
                own = f"{(high << 8)+low:x}"
                int16 = int(own, 16)
                int16s.append(int16)
                # print(f"0x{int16:x} ", end="")
        checksum = int16s[0]
        for i in range(1, len(int16s)):
            checksum = ones_comp_add16(checksum, int16s[i])
        # print(f" result: {checksum}")

    # print(f"0x{raw_bytes_header:2x}")

    def __parse_options(self, options: bytes):
        """ used to parser Options flield """
        # Note: Copied, Option Class, and Option Number are sometimes referred to as a single eight-bit field, the Option Type.
        __ccn, __length = struct.unpack("! B B", options[:2])
        __data = options[2:__length]
        copied = __ccn >> 7
        klass = (__ccn & 96) >> 5
        number = __ccn & 31
        self.options = {
            "Copied": copied,
            "Option Class": klass,
            "Option Number": number,
            "Option Data": __data,
        }

    def raw(self):
        return self.__raw_bytes

    def upper_layer(self):

        return self.__encap

    def serialize(self):
        return dataclasses.asdict(self)

    def __parse_upper_layer_protocol(self, remaining_raw_bytes):

        self.__encap = Protocol_Parser.parse(
            Layer_Protocols.IP_protocols, self.protocol, remaining_raw_bytes
        )


collect_protocols.append((Layer_Protocols.Ethertype, 2048, IPv4))


class IPv6_Ext_Headers(object):
    """ ipv6 extension header extractor """

    EXT_HEADER_LOOKUP = [
        0,  #: "Hop by Hop_Options",
        43,  #: "Routing",
        44,  #: "Fragment",
        50,  #: "Encapsulating Security Payload (ESP)",
        51,  #: "Authentication Header (AH)",
        59,  #: "No Next Header - inspect payload",
        60,  #: "Destination Options",
        135,  #: "Mobility",
        139,  #: "Host Identity Protocol",
        140,  #: "Shim6 Protocol",
        253,  #: "Reserved",
        254,  #: "Reserved",
    ]

    def __init__(self):
        self._headers = []

    def parse_extension_headers(self, next_header, raw_bytes):
        def parse_header(remaining_raw_bytes):
            __next_header, __ext_header_len = struct.unpack(
                "! B B", remaining_raw_bytes[:2]
            )

            return (
                __next_header,
                remaining_raw_bytes[:__ext_header_len],
                remaining_raw_bytes[__ext_header_len:],
            )

        if next_header not in self.EXT_HEADER_LOOKUP:
            # upper-layer protocol
            return self._headers, next_header, raw_bytes
        else:
            # for clarity
            r_raw_bytes = raw_bytes
            ext_header = next_header

            # extract extion until upper layer protocol is reached
            while ext_header in self.EXT_HEADER_LOOKUP:
                # should parse header to append id and data
                new_ext_header, ext_header_data, r_raw_bytes = parse_header(r_raw_bytes)

                # need to implement Extion headers parsers to decode headers
                self._headers.append((ext_header, ext_header_data))
                ext_header = new_ext_header

            return self._headers, ext_header, r_raw_bytes


@dataclass
class IPv6(object):

    description = "Internet Protocol Version 6"
    identifier = 34525
    version: int
    DS: int
    ECN: int
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
        traffic_class = (int.from_bytes(__vtf[:2], sys.byteorder) & 2040) >> 4
        self.DS = traffic_class & 252
        self.ECN = traffic_class & 3

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

        self._raw_bytes = raw_bytes

        # parse upper layer protocol
        self.__parse_upper_layer_protocol(protocol, remaining_raw_bytes)

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):
        return self.__encap

    def serialize(self):
        return json.dumps(self, cls=EnhancedJSONEncoder)

    def __parse_upper_layer_protocol(self, protocol, remaining_raw_bytes):
        # The values are shared with those used for the IPv4 protocol field

        self.__encap = Protocol_Parser.parse(
            Layer_Protocols.IP_protocols, protocol, remaining_raw_bytes
        )


collect_protocols.append((Layer_Protocols.Ethertype, 34525, IPv6))


@dataclass
class ARP(object):
    description = "Address Resolution Protocol"
    identifier = 2054

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

        self._raw_bytes = raw_bytes

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):
        return None

    def serialize(self):
        return dataclasses.asdict(self)

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


collect_protocols.append((Layer_Protocols.Ethertype, 2054, ARP))


@dataclass
class CDP(object):
    description = "Cisco Discovery Protocol"
    identifier = 8192

    def __init__(self, raw_bytes):
        # proprietary protocol
        self._raw_bytes = raw_bytes

    def raw(self):
        return self._raw_bytes

    def serialize(self):
        return dataclasses.asdict(self)

    def upper_layer(self):
        return None


collect_protocols.append((Layer_Protocols.Ethertype, 8192, CDP))


@dataclass
class LLDP(object):

    description = "35020 IEEE Std 802.1AB - Link Layer Discovery Protocol"
    identifier = 35020
    tlvs: list

    def __init__(self, raw_bytes):

        #
        tlv_dict, r_bytes = self.__parse_tlv(raw_bytes)
        self.tlvs = [tlv_dict]
        while tlv_dict["Type"] != 0:
            tlv_dict, r_bytes = self.__parse_tlv(r_bytes)

            self.tlvs.append(tlv_dict)

        self._raw_bytes = raw_bytes

    def __parse_tlv(self, raw_bytes):
        (__tl,) = struct.unpack("! H", raw_bytes[:2])
        type_ = (__tl & 0b1111111000000000) >> 9
        length = __tl & 0b111111111
        value = raw_bytes[2:length]

        return {
            "Type": type_,
            "Length": length,
            "Value": value,
        }, raw_bytes[length:]

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):
        return None

    def serialize(self):
        return dataclasses.asdict(self)


collect_protocols.append((Layer_Protocols.Ethertype, 35020, LLDP))


@dataclass
class IGMP(object):

    description = "Internet Group Management Protocol"
    identifier = 2
    type_: int
    max_resp_time: int
    checksum: int
    group_address: str

    def __init__(self, raw_bytes):
        __tp, __mrt, __chk, __ga = struct.unpack("! B B H 4s", raw_bytes[:8])

        self.type_ = __tp
        self.max_resp_time = __mrt
        self.checksum = __chk
        self.group_address = get_ipv4_addr(__ga)

        self._raw_bytes = raw_bytes
        # need to implement parser for message types

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):
        return None

    def serialize(self):
        return dataclasses.asdict(self)


collect_protocols.append((Layer_Protocols.IP_protocols, 2, IGMP))


@dataclass
class ICMPv6(object):

    description = "Internet Control Message Protocol for IPv6"
    identifier = 58
    type_: int
    code: int
    checksum: int
    message: bytes

    def __init__(self, raw_bytes):
        __tp, __cd, __chk, __msg = struct.unpack("! B B H 4s", raw_bytes[:8])
        self.type_ = __tp
        self.code = __cd
        self.checksum = __chk
        self.message = base64.b64encode(__msg).decode("utf-8")
        self._raw_bytes = raw_bytes

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):
        return None

    def serialize(self):
        return dataclasses.asdict(self)


collect_protocols.append((Layer_Protocols.IP_protocols, 58, ICMPv6))


@dataclass
class ICMP(object):

    description = "Internet Control Message Protocol"
    identifier = 1
    type_: int
    code: int
    checksum: int
    message: bytes

    def __init__(self, raw_bytes):

        __tp, __cd, __chk, __msg = struct.unpack("! B B H 4s", raw_bytes[:8])
        self.type_ = __tp
        self.code = __cd
        self.checksum = __chk

        # implement parser to decode control messages
        self.message = base64.b64encode(__msg).decode("utf-8")
        self._raw_bytes = raw_bytes

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):
        return None

    def serialize(self):
        return dataclasses.asdict(self)


collect_protocols.append((Layer_Protocols.IP_protocols, 1, ICMP))


def get_internet_layer_parsers():
    return collect_protocols