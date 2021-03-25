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
class Packet_802_3(object):
    description = "Ethernet 802.3 Packet"
    dest_MAC: str
    src_MAC: str
    ether_type: int

    def __init__(self, raw_bytes):
        __des_addr, __src_addr, __tp = struct.unpack("! 6s 6s H", raw_bytes[:14])
        self.dest_MAC = get_mac_addr(__des_addr)
        self.src_MAC = get_mac_addr(__src_addr)
        self.ether_type = __tp

        self.__parser_upper_layer_protocol(raw_bytes[14:])

    def __parser_upper_layer_protocol(self, remaining_raw_bytes):

        if self.ether_type >= 0 and self.ether_type <= 1500:
            # logical link control (LLC) Numbers
            self._encap = Packet_802_2(self.ether_type, remaining_raw_bytes)


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
                print(
                    f"AF Packet - proto: {af_packet.proto}, pkttype: {af_packet.pkttype}"
                )

                # check whether WIFI packets are different from ethernet packets
                print(f"802_3 Packet: {Packet_802_3(raw_bytes)}")
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
