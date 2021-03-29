import struct

from dataclasses import dataclass

from .parsers import Protocol_Parser
from .layer import Layer_Protocols


@dataclass
class SNAP_ext(object):
    ...