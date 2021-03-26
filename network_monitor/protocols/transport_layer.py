import struct
import sys
from dataclasses import dataclass

# IGMP, ICMP, ICMPv6 should be defined in internet_layer file. defining here to avoid cicular import
# should be able to fix with parser register implementation


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
class TCP(object):

    description = "Transmission Control Protocol"
    source_port: int
    destination_port: int
    sequence_number: int
    acknowledgment_number: int  # if ACK set
    data_offset: int
    reserved: int
    flags: list
    window_size: int
    checksum: int
    urgent_pointer: int  # if URG set
    # options: bytes

    def __init__(self, raw_bytes):
        # fixed header part
        (
            __src_prt,
            __des_prt,
            __seq_num,
            __ack_num,
            __d_offset_flags,
            __win_size,
            __chk_sum,
            __urg_ptr,
        ) = struct.unpack("! H H L L 2s H H H", raw_bytes[:20])

        self.source_port = __src_prt
        self.destination_port = __des_prt
        self.sequence_number = __seq_num
        self.acknowledgment_number = __ack_num

        self.data_offset = __d_offset_flags[0] >> 4
        self.reserved = (__d_offset_flags[0] & 14) >> 1
        self.flags = (
            int.from_bytes(__d_offset_flags, sys.byteorder) & 511
        )  # added ability to index for specific flags

        self.window_size = __win_size
        self.checksum = __chk_sum
        self.urgent_pointer = __urg_ptr

        # if data_offset is larger than 5 then option present
        if self.data_offset > 5:
            # options field has been set need to extract to get to payload
            # implement extractor
            pass
        else:
            # payload data probabily encrypted
            self._payload = raw_bytes[20:]


@dataclass
class UDP(object):

    description = "User Datagram Protocol"
    source_port: int
    destination_port: int
    length: int
    checksum: int

    def __init__(self, raw_bytes):

        __src_prt, __des_prt, __leng, __chk_sum = struct.unpack(
            "! H H H H", raw_bytes[:8]
        )

        self.source_port = __src_prt
        self.destination_port = __des_prt
        self.length = __leng
        self.checksum = __chk_sum

        # payload data probabily encrypted
        # should be based on length field, This field specifies the length in bytes of the UDP header and UDP data.
        self._payload = raw_bytes[8:]


class IP_Protocols(object):
    """wrapper for the different ipv4 protocols parsers"""

    PROTOCOL_LOOKUP = {
        1: ICMP,
        2: IGMP,
        6: TCP,
        17: UDP,
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
