import queue
import threading


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
                # print(
                #     f"AF Packet - proto: {af_packet.proto}, pkttype: {af_packet.pkttype}"
                # )

                # check whether WIFI packets are different from ethernet packets
                out_packet = Packet_802_3(raw_bytes)
                # print(f"802_3 Packet: {out_packet}")

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
