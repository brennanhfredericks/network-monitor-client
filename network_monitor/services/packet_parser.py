
import threading
import time
import json

from asyncio import Queue

from typing import Dict, Any, Union, List, Optional
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
    """
        Instantiate a new filter

        name: provide a name for the filter
        definition: dictionary containting the keys and values ti match with

    """
    Name: str
    Definition: dict

    def __init__(self, name: str, definition: Union[str, Dict[str, Dict[str, Union[str, int]]]]) -> None:
        self.Name: str = name
        # check if definiion is valid
        self.Definition:  Dict[str, Dict[str, Union[str, int]]
                               ] = self._check_valid_definition(definition)

    def _check_valid_definition(self, definition: Union[str, Dict[str, Dict[str, Union[str, int]]]]) -> Dict[str, Dict[str, Union[str, int]]]:

        if not isinstance(definition, dict):

            # check if str and try to decode to json
            if isinstance(definition, str):
                try:
                    definition: Dict[str, Dict[str, Union[str, int]]] = json.loads(
                        definition)
                except Exception as e:
                    raise ValueError(
                        f"{definition} is not a valid definition: {e}")

            else:
                raise ValueError(f"{definition} is not a valid definition")

        # reoccuring part
        for proto_class_name, proto_attrs in definition.items():

            _cls: Any = Protocol_Parser.get_protocol_class_by_name(
                proto_class_name)

            if not isinstance(proto_attrs, dict):
                raise ValueError(
                    f"{self.name}: {proto_class_name} value ({proto_attrs}) not of type {type(dict())}"
                )

            # check for valid dict  keys (attr name) and value (attr value type)
            for proto_attrs_name, proto_attrs_value in proto_attrs.items():
                __temp: Dict[str, Union[str, int]
                             ] = _cls.__dict__["__annotations__"]
                if not proto_attrs_name in __temp.keys():
                    raise ValueError(
                        f"{proto_attrs_name} not a attribute of {proto_class_name}"
                    )

                assert isinstance(
                    proto_attrs_value, __temp[proto_attrs_name]
                ), f"{proto_attrs_name}:{proto_attrs_value} not of type {__temp[proto_attrs_name]}"

        return definition

    def apply(self, packet: Dict[str, Dict[str, Union[str, int]]]) -> bool:

        res: List[bool] = []
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
    def __init__(self, filter_application_packets=False) -> None:

        self.__filters: List[Filter] = []

    # register filters which is in the form of a dictionary
    def register(self, filter_: Filter) -> None:
        """
        add packet filter
        """
        if isinstance(filter_, list):
            # contain a list of Filter objects
            self.__filters.extend(filter_)
        else:
            # single Filter object
            self.__filters.append(filter_)

    def apply(self, af_packet: AF_Packet, out_packet: Union[Packet_802_3, Packet_802_2]) -> Optional[Dict[str, Dict[str, Union[str, int]]]]:

        # flatten protocols into list for easy seriliazation

        out_protocols: List[Any] = flatten_protocols(out_packet)

        # create list of dictionaries containing definitions
        _p: Dict[str, Dict[str, Union[str, int]]] = {
            Protocol_Parser.get_protocol_name_by_class(p.__class__): p.serialize()
            for p in out_protocols
        }
        # add originating information
        _p["AF_Packet"] = af_packet.serialize()

        res: List[bool] = []
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
        raw_data_queue: Queue,
        processed_queue: Queue,
        packet_filter: Packet_Filter,
    ) -> None:

        self.raw_data_queue = raw_data_queue
        self.processed_data_queue = processed_queue
        self.packet_filter = packet_filter

    async def worker(self) -> None:

        while True:

            raw_bytes, address = await self._data_queue.get()

            # do processing with data
            af_packet: AF_Packet = AF_Packet(address)

            out_packet: Optional[Union[Packet_802_3, Packet_802_2]] = None

            # check for protocol encapsulation based on the ethernet protocol number
            if af_packet.proto >= 0 and af_packet.proto <= 1500:
                # logical link control (LLC) Numbers
                out_packet: Packet_802_2 = Packet_802_2(raw_bytes)
            else:
                # check whether WIFI packets are different from ethernet packets
                out_packet: Packet_802_3 = Packet_802_3(raw_bytes)

            # implement packet filter here before adding data to ouput queue
            packet: Optional[Dict[str, Dict[str, Union[str, int]]]] = self.packet_filter.apply(
                af_packet, out_packet)

            if packet is not None:
                self.processed_data_queue.put(packet)

            # implement stream holder here
