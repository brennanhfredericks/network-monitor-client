import sys
import struct
import base64
import json
import dataclasses
import asyncio

from dataclasses import dataclass
from typing import Union, Dict, Any, List, Tuple, Optional
from aiologger import Logger
from .protocol_utils import (
    get_ipv4_addr,
    get_ipv6_addr,
    get_mac_addr,
    grouper,
    EnhancedJSONEncoder,
)

from .parsers import Protocol_Parser
from .layer import Layer_Protocols


@dataclass
class IPv4(object):

    Description = "Internet Protocol Version 4"
    Identifier = 2048
    Version: int
    IHL: int
    DSCP: int
    ECN: int
    Total_Length: int
    Identification: int
    Flags: int
    Fragment_Offset: int
    TTL: int
    Protocol: int
    Header_Checksum: int
    Source_Address: str
    Destination_Address: str
    Options: dict

    def __init__(self, raw_bytes: bytes) -> None:

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
        self.Version: int = __vihl >> 4

        self.IHL: int = __vihl & 15
        self.__verify_checksum(raw_bytes[: self.IHL * 4])
        self.DSCP: int = (__dsen & 252) >> 2
        self.ECN: int = __dsen & 3
        self.Total_Length: int = __tl
        self.Identification: int = __ident

        self.Flags: int = __flags
        self.Fragment_Offset: int = __ff & 8191
        self.TTL: int = __ttl
        self.Protocol: int = __proto
        self.Header_Checksum: int = __hck
        self.Source_Address: str = get_ipv4_addr(__src)
        self.Destination_Address: str = get_ipv4_addr(__des)

        # Note: If the header length is greater than 5 (i.e., it is from 6 to 15)
        # it means that the options field is present and must be considered.

        if self.IHL > 5:
            # raw bytes contains Option field data
            offset: int = 5 * self.IHL  # 8*4 24 bytes
            options: bytes = raw_bytes[20:offset]

            self.__parse_options(options)
            self.__parse_upper_layer_protocol(raw_bytes[offset:])
        else:
            self.__parse_upper_layer_protocol(raw_bytes[20:])
            self.Options = {}

        self.__raw_bytes: bytes = raw_bytes

    def __verify_checksum(self, raw_bytes_header: bytes) -> None:
        """ verify checksum is correct """

        # https://www.thegeekstuff.com/2012/05/ip-header-checksum/

        raise NotImplemented

    def __parse_options(self, options: bytes) -> None:
        """ used to parser Options flield """
        # Note: Copied, Option Class, and Option Number are sometimes referred to as a single eight-bit field, the Option Type.
        __ccn, __length = struct.unpack("! B B", options[:2])
        __data = options[2:__length]
        copied = __ccn >> 7
        klass = (__ccn & 96) >> 5
        number = __ccn & 31
        self.Options: Dict[str, Union[str, int]] = {
            "Copied": copied,
            "Option Class": klass,
            "Option Number": number,
            "Option Data": base64.b64encode(__data).decode("utf-8"),
        }

    def raw(self) -> bytes:
        return self.__raw_bytes

    def upper_layer(self) -> Any:

        return self.__encap

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)

    def __parse_upper_layer_protocol(self, remaining_raw_bytes: bytes) -> None:

        self.__encap: Any = Protocol_Parser.parse(
            Layer_Protocols.IP_protocols, self.Protocol, remaining_raw_bytes
        )


Protocol_Parser.register(Layer_Protocols.Ethertype, 2048, IPv4)


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

    def __init__(self) -> None:
        self._headers: List[Any] = []

    def parse_extension_headers(self, next_header: int, raw_bytes: bytes) -> Tuple[Any, int, bytes]:
        def parse_header(remaining_raw_bytes: bytes) -> Tuple[int, bytes, bytes]:
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
                new_ext_header, ext_header_data, r_raw_bytes = parse_header(
                    r_raw_bytes)

                # need to implement Extion headers parsers to decode headers
                self._headers.append(
                    (ext_header, base64.b64encode(ext_header_data).decode("utf-8"))
                )
                ext_header = new_ext_header

            return self._headers, ext_header, r_raw_bytes


@dataclass
class IPv6(object):

    Description = "Internet Protocol Version 6"
    Identifier = 34525
    Version: int
    DS: int
    ECN: int
    Flow_Label: int
    Payload_Length: int
    Next_Header: int
    Hop_Limit: int
    Source_Address: str
    Destination_Address: str
    Ext_Headers: list

    def __init__(self, raw_bytes: bytes) -> None:

        # parse fixed header
        __vtf, __pl_len, __next_h, __hop_l, __src_addr, __des_addr = struct.unpack(
            "! 4s H B B 16s 16s", raw_bytes[:40]
        )

        # index first byte
        self.Version: int = __vtf[0] >> 4
        traffic_class = (int.from_bytes(__vtf[:2], sys.byteorder) & 2040) >> 4
        self.DS: int = traffic_class & 252
        self.ECN: int = traffic_class & 3

        self.Flow_Label: int = int.from_bytes(
            __vtf[1:4], sys.byteorder) & 1048575
        self.Payload_Length: int = __pl_len
        self.Next_Header: int = __next_h
        self.Hop_Limit: int = __hop_l
        self.Source_Address: str = get_ipv6_addr(__src_addr)
        self.Destination_Address: str = get_ipv6_addr(__des_addr)

        # parse extension headers
        (
            self.Ext_Headers,
            protocol,
            remaining_raw_bytes,
        ) = IPv6_Ext_Headers().parse_extension_headers(self.Next_Header, raw_bytes[40:])

        self._raw_bytes: bytes = raw_bytes

        # parse upper layer protocol
        self.__parse_upper_layer_protocol(protocol, remaining_raw_bytes)

    def raw(self) -> bytes:
        return self._raw_bytes

    def upper_layer(self) -> Any:
        return self.__encap

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)

    def __parse_upper_layer_protocol(self, protocol, remaining_raw_bytes: bytes) -> None:
        # The values are shared with those used for the IPv4 protocol field

        self.__encap: Any = Protocol_Parser.parse(
            Layer_Protocols.IP_protocols, protocol, remaining_raw_bytes
        )


Protocol_Parser.register(Layer_Protocols.Ethertype, 34525, IPv6)


@dataclass
class ARP(object):
    description = "Address Resolution Protocol"
    identifier = 2054

    HTYPE: int
    PTYPE: int
    HLEN: int
    PLEN: int
    Operation: int
    SHA: str
    SPA: str
    THA: str
    TPA: str

    def __init__(self, raw_bytes: bytes) -> None:
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

        self.HTYPE: int = __hardware_type
        self.PTYPE: int = __protocol_type
        self.HLEN: int = __hlen
        self.PLEN: int = __plen
        self.Operation: int = __op_code
        self.SHA: str = get_mac_addr(__sender_hw_addr)
        self.SPA: str = self._decode_protocol_addr(__sender_proto_addr)
        self.THA: str = get_mac_addr(__target_hw_addr)
        self.TPA: str = self._decode_protocol_addr(__target_proto_addr)

        self._raw_bytes: bytes = raw_bytes

    def raw(self) -> bytes:
        return self._raw_bytes

    def upper_layer(self) -> Optional[Any]:
        return None

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)

    def _decode_protocol_addr(self, proto_addr: int) -> str:
        logger = Logger.with_default_handlers()
        if self.PTYPE == 2048:
            return get_ipv4_addr(proto_addr)
        elif self.PTYPE == 34525:
            return get_ipv6_addr(proto_addr)
        else:
            # add logging functionality here
            asyncio.create_task(logger.warning(
                f" address ARP decoding not implemented for {self.PTYPE}, address {proto_addr}"
            ))
            return str(proto_addr)


Protocol_Parser.register(Layer_Protocols.Ethertype, 2054, ARP)


@dataclass
class CDP(object):
    Description = "Cisco Discovery Protocol"
    Identifier = 8192

    def __init__(self, raw_bytes: bytes) -> None:
        # proprietary protocol
        self._raw_bytes: bytes = raw_bytes

    def raw(self) -> bytes:
        return self._raw_bytes

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)

    def upper_layer(self) -> Optional[Any]:
        return None


Protocol_Parser.register(Layer_Protocols.Ethertype, 8192, CDP)


@dataclass
class LLDP(object):

    Description = "35020 IEEE Std 802.1AB - Link Layer Discovery Protocol"
    Identifier = 35020
    TLV: list

    def __init__(self, raw_bytes: bytes) -> None:

        tlv_dict, r_bytes = self.__parse_tlv(raw_bytes)
        self.TLV: List[Dict[str, Union[str, int]]] = [tlv_dict]
        while int(tlv_dict["Type"]) != 0:
            tlv_dict, r_bytes = self.__parse_tlv(r_bytes)

            self.TLV.append(tlv_dict)

        self._raw_bytes: bytes = raw_bytes

    def __parse_tlv(self, raw_bytes: bytes) -> Tuple[Dict[str, Union[str, int]], bytes]:
        (__tl,) = struct.unpack("! H", raw_bytes[:2])
        type_ = (__tl & 0b1111111000000000) >> 9
        length = __tl & 0b111111111
        value = raw_bytes[2:length]

        return {
            "Type": type_,
            "Length": length,
            "Value": base64.b64encode(value).decode("utf-8"),
        }, raw_bytes[length:]

    def raw(self) -> bytes:
        return self._raw_bytes

    def upper_layer(self) -> Optional[Any]:
        return None

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)


Protocol_Parser.register(Layer_Protocols.Ethertype, 35020, LLDP)


@dataclass
class Xerox(object):
    Description = "Xerox Experimental"
    Identifier = 103
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


Protocol_Parser.register(Layer_Protocols.Ethertype, 103, Xerox)


@dataclass
class IGMP(object):

    Description = "Internet Group Management Protocol"
    Identifier = 2
    Type: int
    Max_Response_Time: int
    Checksum: int
    Group_Address: str

    def __init__(self, raw_bytes: bytes) -> None:
        __tp, __mrt, __chk, __ga = struct.unpack("! B B H 4s", raw_bytes[:8])

        self.Type: int = __tp
        self.Max_Response_Time: int = __mrt
        self.Checksum: int = __chk
        self.Group_Address: str = get_ipv4_addr(__ga)

        self._raw_bytes: bytes = raw_bytes
        # need to implement parser for message types

    def raw(self) -> bytes:
        return self._raw_bytes

    def upper_layer(self) -> Optional[Any]:
        return None

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)


Protocol_Parser.register(Layer_Protocols.IP_protocols, 2, IGMP)


@dataclass
class ICMPv6(object):

    Description = "Internet Control Message Protocol for IPv6"
    Identifier = 58
    Type: int
    Code: int
    Checksum: int
    Message: str

    def __init__(self, raw_bytes: bytes) -> None:
        __tp, __cd, __chk, __msg = struct.unpack("! B B H 4s", raw_bytes[:8])
        self.Type: int = __tp
        self.Code: int = __cd
        self.Checksum: int = __chk
        self.Message: str = base64.b64encode(__msg).decode("utf-8")
        self._raw_bytes: bytes = raw_bytes

    def raw(self) -> bytes:
        return self._raw_bytes

    def upper_layer(self) -> Optional[Any]:
        return None

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)


Protocol_Parser.register(Layer_Protocols.IP_protocols, 58, ICMPv6)


@dataclass
class ICMP(object):

    Description = "Internet Control Message Protocol"
    Identifier = 1
    Type: int
    Code: int
    Checksum: int
    Message: str

    def __init__(self, raw_bytes: bytes) -> None:

        __tp, __cd, __chk, __msg = struct.unpack("! B B H 4s", raw_bytes[:8])
        self.Type: int = __tp
        self.Code: int = __cd
        self.Checksum: int = __chk

        # implement parser to decode control messages
        self.Message = base64.b64encode(__msg).decode("utf-8")
        self._raw_bytes: bytes = raw_bytes

    def raw(self) -> bytes:
        return self._raw_bytes

    def upper_layer(self) -> Optional[Any]:
        return None

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)


Protocol_Parser.register(Layer_Protocols.IP_protocols, 1, ICMP)
