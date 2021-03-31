import queue
import threading
import time
import requests

from network_monitor.filters import flatten_protocols


class Packet_Submitter(object):
    """ class for storing and submitting packets"""

    def __init__(
        self, output_queue: queue.Queue, url: str = "http://192.168.88.52/packets"
    ):
        self._data_queue = output_queue
        self._url = url

    def _submitter(self):
        re_try_timer = 60
        while self._sentinal or not self._data_queue.empty():

            if not self._data_queue.empty():
                out_packet = self._data_queue.get()

                # create a list of all the protocols contain in the packet
                f_protocols = flatten_protocols(out_packet)

                # format data for post request
                payload = {}
                for f in f_protocols:
                    payload[f.identifier] = f.serialize()

                post_success = False
                # try post quest
                try:
                    r = requests.post(self._url, data=payload, timeout=0.001)
                except Exception as e:
                    # print(e)
                    ...
                else:
                    if r.status_code == 200:
                        post_success = True

                # log to file if post failed, try every x minutes, delete when transfered
                if not post_success:
                    print("failed to post file")

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
