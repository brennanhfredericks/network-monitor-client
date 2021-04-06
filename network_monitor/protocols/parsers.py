import os
import time
import binascii
from .protocol_utils import Unknown

from .layer import Layer_Protocols


class Parser:
    """ class to register all packet parsers for various levels"""

    __protocol_parsers = {}
    __protocol_str_lookup = {}

    def __init__(self, log_dir="./logger_output/unknown_protocols/"):

        # init layer protocols
        for layer_protocol in Layer_Protocols:
            self.__protocol_parsers[layer_protocol] = {}
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.__fname = os.path.join(
            log_dir, f"raw_unknown_protocols_{int(time.time())}.lp"
        )

    @property
    def parsers(self):

        return self.__protocol_parsers

    def register(self, layer, identifier, protocol_parser):
        # check if dataclass and callable
        self.__protocol_parsers[layer][identifier] = protocol_parser
        self.__protocol_str_lookup[protocol_parser.__name__] = protocol_parser

    def get_protocol_by_class_name(self, class_name: str):

        """ return an empty protocol class used in comparison """
        print(self.__protocol_str_lookup)
        try:
            res = self.__protocol_str_lookup[class_name]
        except IndexError as e:
            # add logging functionality
            raise ValueError(f"{class_name} not a vaild protocol class name")
        else:
            return res

    def parse(self, layer, identifier, raw_bytes):
        """ use to register parser"""
        try:
            return self.__protocol_parsers[layer][identifier](raw_bytes)
            # print(f"parsed: {self._encap}")
        except KeyError as e:

            with open(self.__fname, "ab") as fout:
                info = f"{layer}_{identifier}"
                fout.write(binascii.b2a_base64(info.encode()))
                fout.write(binascii.b2a_base64(raw_bytes))
            print(
                f"Protocol Not Implemented - Layer: {layer}, identifier: {identifier}"
            )
            return Unknown("no protocol parser available", identifier, raw_bytes)


Protocol_Parser = Parser()


def register_parsers():
    from .internet_layer import get_internet_layer_parsers
    from .transport_layer import get_transport_layer_parsers
    from .lsap_addresses import get_LLC_layer_parsers

    parsers = []
    parsers += get_internet_layer_parsers()
    parsers += get_transport_layer_parsers()
    parsers += get_LLC_layer_parsers()

    for layer, identifier, protocol_parser in parsers:
        Protocol_Parser.register(layer, identifier, protocol_parser)


register_parsers()