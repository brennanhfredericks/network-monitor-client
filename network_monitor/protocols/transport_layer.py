import struct
import sys
import json
import base64
import dataclasses
from dataclasses import dataclass

from typing import Any, Dict, Union, Optional

from .layer import Layer_Protocols
from .protocol_utils import EnhancedJSONEncoder

from .parsers import Protocol_Parser


@dataclass
class TCP(object):

    Description = "Transmission Control Protocol"
    Identifier = 6
    Source_Port: int
    Destination_Port: int
    Sequence_Number: int
    Acknowledgement_Number: int  # if ACK set
    Data_Offset: int
    Reserved: int
    Flags: dict
    Window_Size: int
    Checksum: int
    Urgent_Pointer: int  # if URG set
    Options: dict
    Payload_Size: int

    def __init__(self, raw_bytes: bytes) -> None:
        # fixed header part
        (
            __src_prt,
            __des_prt,
            __seq_num,
            __ack_num,
            __d_offset_reserved_ns,
            _flags,
            __win_size,
            __chk_sum,
            __urg_ptr,
        ) = struct.unpack("! H H L L B B H H H", raw_bytes[:20])

        self.Source_Port: int = __src_prt
        self.Destination_Port: int = __des_prt
        self.Sequence_Number: int = __seq_num
        self.Acknowledgement_Number: int = __ack_num

        self.Data_Offset: int = __d_offset_reserved_ns >> 4
        self.Reserved: int = (__d_offset_reserved_ns & 14) >> 1
        self.__parse_flags(__d_offset_reserved_ns & 1, _flags)

        self.Window_Size: int = __win_size
        self.Checksum: int = __chk_sum
        self.Urgent_Pointer: int = __urg_ptr

        self._raw_bytes: bytes = raw_bytes
        self._payload: Optional[bytes] = None
        # if data_offset is larger than 5 then option present
        if self.Data_Offset > 5:
            # options field has been set need to extract to get to payload
            # implement extractor
            offset = 5 * self.Data_Offset
            raw_options = raw_bytes[20:offset]
            self.__parse_options(raw_options)

            self._payload = raw_bytes[offset:]

        else:
            # payload data probabily encrypted
            self.Options: Dict[str, Union[str, int]] = {}
            self._payload = raw_bytes[20:]

        self.Payload_Size = len(self._payload)

    def __parse_flags(self, ns_flag: int, other_flags: int) -> None:
        self.Flags: Dict[str, int] = {
            "NS": ns_flag,
            "CWR": (other_flags & 128) >> 7,
            "ECE": (other_flags & 64) >> 6,
            "URG": (other_flags & 32) >> 5,
            "ACK": (other_flags & 16) >> 4,
            "PSH": (other_flags & 8) >> 3,
            "RST": (other_flags & 4) >> 2,
            "SYN": (other_flags & 2) >> 1,
            "FIN": (other_flags & 1)
        }

    def __parse_options(self, raw_options_bytes) -> None:
        # Option-Kind (1 byte), Option-Length (1 byte), Option-Data (variable).
        __kind, __length = struct.unpack("! B B", raw_options_bytes[:2])
        __data = raw_options_bytes[2:__length]

        self.Options: Dict[str, Union[str, int, Dict[str, Union[str, int]]]] = {
            "Option-Kind": __kind,
            "Option-Length": __length,
            "Option-Data": base64.b64encode(__data).decode("utf-8"),
        }

    def raw(self) -> bytes:
        return self._raw_bytes

    def upper_layer(self) -> Optional[Any]:
        return None

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)


Protocol_Parser.register(Layer_Protocols.IP_protocols, 6, TCP)


@dataclass
class UDP(object):

    Description = "User Datagram Protocol"
    Identifier = 17
    Source_Port: int
    Destination_Port: int
    Length: int
    Checksum: int
    Payload_Size: int

    def __init__(self, raw_bytes: bytes) -> None:

        __src_prt, __des_prt, __leng, __chk_sum = struct.unpack(
            "! H H H H", raw_bytes[:8]
        )

        self.Source_Port: int = __src_prt
        self.Destination_Port: int = __des_prt
        self.Length: int = __leng
        self.Checksum: int = __chk_sum

        self._raw_bytes: bytes = raw_bytes
        # payload data probabily encrypted
        # should be based on length field, This field specifies the length in bytes of the UDP header and UDP data.
        # print(self.length, len(self._raw_bytes))
        self._payload: bytes = raw_bytes[8:]
        self.Payload_Size = len(self._payload)

    def raw(self) -> bytes:
        return self._raw_bytes

    def upper_layer(self) -> Optional[None]:

        return None

    def serialize(self) -> Dict[str, Union[str, int]]:
        return dataclasses.asdict(self)


Protocol_Parser.register(Layer_Protocols.IP_protocols, 17, UDP)
