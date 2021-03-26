import queue
import threading
import time

from ..protocols import AF_Packet, Packet_802_3, Packet_802_2


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
