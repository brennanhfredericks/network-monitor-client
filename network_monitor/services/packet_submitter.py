import queue
import threading
import time

from network_monitor.filters import flatten_protocols


class Packet_Submitter(object):
    """ class for storing and submitting packets"""

    def __init__(self, output_queue: queue.Queue):
        self._data_queue = output_queue

    def _submitter(self):
        re_try_timer = 60
        while self._sentinal or not self._data_queue.empty():

            if not self._data_queue.empty():
                out_packet = self._data_queue.get()

                # create a list of all the protocols contain in the packet
                f_protocols = flatten_protocols(out_packet)

                # format data for post request
                print(f_protocols)

                # try post quest

                # log to file if fail, try every x minutes, delete when transfered
            else:
                time.sleep(0.1)

    def start(self):
        self._sentinal = True

        self._thread_handle = threading.Thread(
            target=self._submitter, name="packet submitter", daemon=False
        )

        self._thread_handle.start()

    def stop(self):
        self._sentinal = False
        self._thread_handle.join()
