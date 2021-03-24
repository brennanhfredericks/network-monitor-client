import queue
import time
import threading
import socket
import binascii
from dataclasses import dataclass


def get_ipv4_addr(addr):
    return ".".join(map(str,addr))

def get_mac_addr (addr):
    addr_str = map('{:02x}'.format,addr)
    return ':'.join(addr_str).upper()

def get_ipv6_addr(addr):
    addr_str = [binascii.b2a_hex(x).decode("utf-8") for x in struct.unpack("! 2s 2s 2s 2s 2s 2s 2s 2s",addr)]
    return ":".join(addr_str)

PKTTYPE_LOOKUP ={
    socket.PACKET_BROADCAST: "PACKET_BROADCAST",
    socket.PACKET_FASTROUTE: "PACKET_FASTROUTE",
    socket.PACKET_HOST: "PACKET_HOST",
    socket.PACKET_MULTICAST: "PACKET_MULTICAST",
    socket.PACKET_OTHERHOST: "PACKET_OTHERHOST",
    socket.PACKET_OUTGOING: "PACKET_OUTGOING",
}

@dataclass
class AF_Packet:
    """ Class for parsing low level packets"""
    ifname: str
    proto: int
    pkttype: str
    hatype: int
    hwaddr: str

    def __init__(self,address):
        
        self.ifname = address[0]
        self.proto = address[1]
        self.pkttype = PKTTYPE_LOOKUP[address [2]]
        self.hatype = address[3]
        self.hwaddr = get_mac_addr(address[4])
        

class Packet_Parser(object):
    """ Class for processing bytes packets"""
    def __init__(self, data_queue: queue.Queue, output_queue: queue.Queue = None):

        self.data_queue = data_queue

    def _packet_info(self):
        pass

    def _parser(self):
        
        # clearout data_queue before exiting loop
        while self._sentinal or not self.data_queue.empty():

            if not self.data_queue.empty():
                raw_bytes, address = self.data_queue.get()
                print(AF_Packet(address))
                # do processing with data
            else:
                # sleep for 100ms
                time.sleep(0.1)

    def start(self):
        self._sentinal = True
        self._thread_handle = threading.Thread(target=self._parser,name="packet parser",daemon=False)
        self._thread_handle.start()

    def stop(self):
        self._sentinal = False
        self._thread_handle.join()
