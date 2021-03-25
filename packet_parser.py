import queue
import time
import threading
import socket
import binascii
import struct

from dataclasses import dataclass


def get_ipv4_addr(addr):
    return ".".join(map(str, addr))


def get_mac_addr(addr):
    addr_str = map("{:02x}".format, addr)
    return ":".join(addr_str).upper()


def get_ipv6_addr(addr):
    addr_str = [
        binascii.b2a_hex(x).decode("utf-8")
        for x in struct.unpack("! 2s 2s 2s 2s 2s 2s 2s 2s", addr)
    ]
    return ":".join(addr_str)


PKTTYPE_LOOKUP = {
    socket.PACKET_BROADCAST: "PACKET_BROADCAST",
    socket.PACKET_FASTROUTE: "PACKET_FASTROUTE",
    socket.PACKET_HOST: "PACKET_HOST",
    socket.PACKET_MULTICAST: "PACKET_MULTICAST",
    socket.PACKET_OTHERHOST: "PACKET_OTHERHOST",
    socket.PACKET_OUTGOING: "PACKET_OUTGOING",
}


@dataclass
class Unknown(object):
    description = "Unknown Protocol"
    message: str


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
class ICMP(object):

    description = "Internet Control Message Protocol"
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
        self.message = __msg


@dataclass
class ICMPv6(object):
    description = "Internet Control Message Protocol for IPv6"
    type_: int
    code: int
    checksum: int
    message: bytes

    def __init__(self, raw_bytes):
        __tp, __cd, __chk, __msg = struct.unpack("! B B H 4s", raw_bytes[:8])
        self.type = __tp
        self.code = __cd
        self.checksum = __chk.decode("latin-1")
        self.message = __msg.decode("latin-1")


@dataclass
class IGMP(object):
    description = "Internet Group Management Protocol"
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

        # need to implement parser for message types


class IPv4_Protocols(object):
    """wrapper for the different ipv4 protocols parsers"""

    PROTOCOL_LOOKUP = {
        1: ICMP,
        2: IGMP,
        58: ICMPv6,
    }

    def __init__(self, protocol, raw_bytes):

        try:
            self._encap = self.PROTOCOL_LOOKUP[protocol](raw_bytes)
            print(self._encap)
        except KeyError:
            # would any other exception occur?
            # add loggin functionality here
            self._encap = Unknown(
                f"Parser for IPv4 protocal {protocol} not implemented"
            )
            print(f"Parser for IPv4 protocal {protocol} not implemented")


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

        self._encap = IPv4_Protocols(self.protocol, remaining_raw_bytes)


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


class IPv6_Ext_Headers(object):
    """ wrapper for the different ipv6 extension headers """

    # hack need specify callable objects
    EXT_HEADER_LOOKUP = {
        0: "Hop by Hop_Options",
        43: "Routing",
        44: "Fragment",
        50: "Encapsulating Security Payload (ESP)",
        51: "Authentication Header (AH)",
        59: "No Next Header - inspect payload",
        60: "Destination Options",
        135: "Mobility",
        139: "Host Identity Protocol",
        140: "Shim6 Protocol",
        253: "Reserved",
        254: "Reserved",
    }

    def __init__(self):
        self._headers = []

    def parse_extension_headers(self, next_header, raw_bytes):
        # When extension headers are present in the packet this field indicates which extension header follows.
        # The values are shared with those used for the IPv4 protocol field, as both fields have the same function
        # If a node does not recognize a specific extension header, it should discard the packet and send a Parameter Problem message (ICMPv6 type 4, code 1).
        # Value 59 (No Next Header) in the Next Header field indicates that there is no next header whatsoever following this one, not even a header of an upper-layer protocol. It means that, from the header's point of view, the IPv6 packet ends right after it: the payload should be empty.[1] There could, however, still be data in the payload if the payload length in the first header of the packet is greater than the length of all extension headers in the packet. This data should be ignored by hosts, but passed unaltered by routers.

        def parse_header(remaining_raw_bytes):
            __next_header, __ext_header_len = struct.unpack(
                "! B B", remaining_raw_bytes[:2]
            )

            return (
                __next_header,
                remaining_raw_bytes[:__ext_header_len],
                remaining_raw_bytes[__ext_header_len:],
            )

        if next_header not in self.EXT_HEADER_LOOKUP.keys():
            # upper-layer protocol
            return self._headers, next_header, raw_bytes
        else:
            # for clarity
            r_raw_bytes = raw_bytes
            ext_header = next_header

            # extract extion until upper layer protocol is reached
            while ext_header in self.EXT_HEADER_LOOKUP.keys():
                # should parse header to append id and data
                new_ext_header, ext_header_data, r_raw_bytes = parse_header(r_raw_bytes)

                # need to implement Extion headers parsers to decode headers
                self._headers.append((ext_header, ext_header_data))
                ext_header = new_ext_header

            return self._headers, ext_header, r_raw_bytes


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
        __vtf, __pl_len, __next_h, __hop_l, __src_addr, __des_addr = struct.unpack(
            "! 4s H B B 16s 16s", raw_bytes[:40]
        )

        # parse fixed header

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

        self.__parser_upper_layer_protocol(raw_bytes[14:])

    def __parser_upper_layer_protocol(self, remaining_raw_bytes):

        if self.ethertype >= 0 and self.ethertype <= 1500:
            # logical link control (LLC) Numbers
            self._encap = Packet_802_2(self.ethertype, remaining_raw_bytes)
        else:
            self._encap = Ethertype(self.ethertype, remaining_raw_bytes)


@dataclass
class Packet_802_2(object):

    description = "Ethernet 802.2 LLC Packet"
    DSAP: str
    SSAP: str
    control: str
    OUI: str
    protocol_id: int

    def __init__(self, ether_type, raw_bytes):
        # could be unpacking this wrong need to verify
        # __dsap, __ssap, __ctl, __oi, __code = struct.unpack(
        #     "! c c c 3s H", raw_bytes[:8]
        # )

        # alternative unpacking
        __dsap, __ssap, __ctl, __oi, __code = struct.unpack(
            "! c c 2s 3s H", raw_bytes[:9]
        )

        # 802.2 LLC Header
        self.DSAP = binascii.b2a_hex(__dsap)
        self.SSAP = binascii.b2a_hex(__ssap)
        self.control = binascii.b2a_hex(__ctl)

        # SNAP extension
        self.OUI = binascii.b2a_hex_(__oui)
        self.protocol_id = __code

        self.__parser_upper_layer_protocol(raw_bytes[9:])

    def __parser_upper_layer_protocol(self, remaining_raw_bytes):
        # not parser out, need to investigate futher
        self.__encap = remaining_raw_bytes


class Packet_Parser(object):
    """ Class for processing bytes packets"""

    def __init__(self, data_queue: queue.Queue, output_queue: queue.Queue = None):

        self.data_queue = data_queue

    def _parser(self):

        # clearout data_queue before exiting loop
        while self._sentinal or not self.data_queue.empty():

            if not self.data_queue.empty():
                raw_bytes, address = self.data_queue.get()

                # do processing with data
                af_packet = AF_Packet(address)
                # print(
                #     f"AF Packet - proto: {af_packet.proto}, pkttype: {af_packet.pkttype}"
                # )

                # check whether WIFI packets are different from ethernet packets
                out_packet = Packet_802_3(raw_bytes)
                # print(f"802_3 Packet: {out_packet}")

            else:
                # sleep for 100ms
                time.sleep(0.1)

    def start(self):
        self._sentinal = True
        self._thread_handle = threading.Thread(
            target=self._parser, name="packet parser", daemon=False
        )
        self._thread_handle.start()

    def stop(self):
        self._sentinal = False
        self._thread_handle.join()
