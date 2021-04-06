import queue
import threading
import time
from dataclasses import dataclass

from ..protocols import AF_Packet, Packet_802_3, Packet_802_2, Protocol_Parser

from ..filters.deep_walker import flatten_protocols

"""
    Packet Filter 

    Implemeting packet filter

    - get all information from attrs and value from class lookup and match to input

    - get all information from key and value using flatten_protocols into list and match input 
        - seriliaze protocols into dict, i.e. move step from submiter to filter,
        - filter input is provide as a dict
        - i.e {IPv4:{destination:192.168.124.26}}
        - match dict based on keys and values
"""


@dataclass
class Filter(object):
    name: str
    definition: list

    def __init__(self, name, definition):
        self.name = name
        # check if definiion is valid
        self.definition = self._check_valid_definition(definition)

    def _check_valid_definition(self, definition):
        assert isinstance(
            definition, dict
        ), f"{definition} is not of type {type(dict)}, it have type {type(definition)} "

        # reoccuring part
        for proto_class_name, proto_attrs in definition.items():

            _cls = Protocol_Parser.get_protocol_class_by_name(proto_class_name)

            if not isinstance(proto_attrs, dict):
                raise ValueError(
                    f"{self.name}: {proto_class_name} value ({proto_attrs}) not of type {type(dict)}"
                )

            # check for valid dict  keys (attr name) and value (attr value type)
            for proto_attrs_name, proto_attrs_value in proto_attrs.items():
                __temp = _cls.__dict__["__annotations__"]
                if not proto_attrs_name in __temp.keys():
                    raise ValueError(
                        f"{proto_attrs_name} not a attribute of {proto_class_name}"
                    )

                assert isinstance(
                    proto_attrs_value, __temp[proto_attrs_name]
                ), f"{proto_attrs_name}:{proto_attrs_value} not of type {__temp[proto_attrs_name]}"

        return definition

    def apply(self, packet):

        res = []

        for proto_name, proto_attrs in self.definition.items():
            if proto_name in packet.keys():
                if not proto_attrs:
                    res.append(True)
                else:
                    try:
                        next(
                            False
                            for k, v in proto_attrs.items()
                            if packet[proto_name][k] != v
                        )
                    except StopIteration:
                        res.append(True)
                    else:
                        res.append(False)
            else:
                res.append(False)

        # single filter all protocols should match
        return all(res)


class Packet_Filter(object):
    def __init__(self, filter_application_packets=False):

        self.__filters = []

    # register filters which is in the form of a dictionary
    def register(self, filter_: Filter):
        """
        add packet filter
        """
        self.__filters.append(filter_)

    def apply(self, af_packet, out_packet) -> bool:

        # flatten protocols into list for easy seriliazation

        out_protocols = flatten_protocols(out_packet)

        # create list of dictionaries containing definitions
        _p = {
            Protocol_Parser.get_protocol_name_by_class(p.__class__): p.serialize()
            for p in out_protocols
        }

        _p["AF_Packet"] = af_packet

        res = []
        for filter_ in self.__filters:
            res.append(filter_.apply(_p))

        if any(res):
            return None
        else:
            return _p


class Packet_Parser(object):
    """ Class for processing bytes packets"""

    def __init__(
        self,
        data_queue: queue.Queue,
        output_queue: queue.Queue,
        packet_filter: Packet_Filter,
    ):

        self._data_queue = data_queue
        self._output_queue = output_queue
        self._packet_filter = packet_filter

    def _parser(self):

        # clearout data_queue before exiting loop
        while self._sentinal or not self._data_queue.empty():

            if not self._data_queue.empty():
                raw_bytes, address = self._data_queue.get()

                # do processing with data
                af_packet = AF_Packet(address)

                out_packet = None

                if af_packet.proto >= 0 and af_packet.proto <= 1500:
                    # logical link control (LLC) Numbers
                    out_packet = Packet_802_2(raw_bytes)
                else:
                    # check whether WIFI packets are different from ethernet packets
                    out_packet = Packet_802_3(raw_bytes)

                # implement packet filter here before adding data to ouput queue
                packet = self._packet_filter.apply(af_packet, out_packet)

                if packet is not None:
                    self._output_queue.put(packet)

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
