import struct
import sys
from dataclasses import dataclass
from .layer import Layer_Protocols

collect_protocols = []  # (level,identifier,parser)


@dataclass
class TCP(object):

    description = "Transmission Control Protocol"
    identifier = 6
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
    options: dict

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

        self._raw_bytes = raw_bytes

        # if data_offset is larger than 5 then option present
        if self.data_offset > 5:
            # options field has been set need to extract to get to payload
            # implement extractor
            offset = 5 * self.data_offset
            raw_options = raw_bytes[20:offset]
            self.__parse_options(raw_options)

            self._payload = raw_bytes[offset:]
        else:
            # payload data probabily encrypted
            self.options = {}
            self._payload = raw_bytes[20:]

    def __parse_options(self, raw_options_bytes):
        # Option-Kind (1 byte), Option-Length (1 byte), Option-Data (variable).
        __kind, __length = struct.unpack("! B B", raw_options_bytes[:2])
        __data = raw_options_bytes[2:__length]

        self.options = {
            "Option-Kind": __kind,
            "Option-Length": __length,
            "Option-Data": __data,
        }

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):
        return None


collect_protocols.append((Layer_Protocols.IP_protocols, 6, TCP))


@dataclass
class UDP(object):

    description = "User Datagram Protocol"
    identifier = 17
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

        self._raw_bytes = raw_bytes
        # payload data probabily encrypted
        # should be based on length field, This field specifies the length in bytes of the UDP header and UDP data.
        # print(self.length, len(self._raw_bytes))
        self._payload = raw_bytes[8:]

    def raw(self):
        return self._raw_bytes

    def upper_layer(self):

        return None


collect_protocols.append((Layer_Protocols.IP_protocols, 17, UDP))


def get_transport_layer_parsers():
    return collect_protocols