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
        self._check_valid_definition(definition)
        self.definition = definition

    def _check_valid_definition(self, definition):
        for defin in definition:

            if not isinstance(defin, dict):
                raise ValueError(f"{self.name}: def_ not of type dict")

            # reoccuring part
            for proto_class_name, proto_attrs in defin.items():

                _cls = Protocol_Parser.get_protocol_by_class_name(proto_class_name)

                if not isinstance(proto_attrs, dict):
                    raise ValueError(
                        f"{self.name}: {proto_class_name} value ({proto_attrs}) not of type dict"
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


class Packet_Filter(object):
    def __init__(self, filter_application_packets=False):

        # could be ordered dict to retain the insertion order
        """
        [
            AF_Packet: {
                ifname:br1,
                proto: 2048,
                pkttype: PACKET_OUTGOING,
                        },
            Packet_802_3: {
                dest_MAC : 45:AF:FF:DF:58
                src_MAC: 45:AF:FF:DF:55
                ethertype: 2048
            },
            IPv4:{
                destination_address: 192.168.60.51,
                source_address: 192.168.87.42,
                },
            TCP: {
                source_port: 50,
                destination_port: 5000
            }
        ]
        """
        self.__filters = []

    # register filters which is in the form of a dictionary
    def register(self, filter_: Filter):
        """
        add packet filter
        """
        self.__filters.append(filter_)

    def apply(self, origin_address, packet):

        # flatten protocols into list for easy seriliazation
        _packet = flatten_protocols(packet)

        # create list of dictionaries containing definitions
        #      :{}
        _p = [{p.__class__: p.serialize()} for p in _packet]

        print(_p)

    # - submit packet to filter
    # - convert packet to list of protocols
    # - convert list of protocols to dict
    # - loop through filters and try to match keys and then values


class Packet_Parser(object):
    """ Class for processing bytes packets"""

    def __init__(self, data_queue: queue.Queue, output_queue: queue.Queue):

        self._data_queue = data_queue
        self._output_queue = output_queue

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

                self._output_queue.put(out_packet)

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
