import queue
import threading
import time
import requests
import os
import base64
from io import StringIO

from network_monitor.filters import flatten_protocols


class Submitter(object):
    """ responsible for submitting data and retrying  """

    def __init__(self, url: str, log_dir, n_buffer: int = 50, re_try_interval=60 * 5):

        self.url = url

        # check
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        else:
            # check if files in directory. if files process and send to server
            out_files = os.listdir(log_dir)
            if len(out_files) > 0:
                # process existing files
                ...
        self.log_dir = log_dir

        self.out_file = f"out_{int(time.time())}.lsp"

        self.n_buffer = n_buffer
        self._buffer = StringIO()

    # submit data to server asynchronously

    # write data to buffer


class Packet_Submitter(object):
    """ class for storing and submitting packets"""

    def __init__(
        self,
        output_queue: queue.Queue,
        url: str = "http://192.168.88.52/packets",
        log_dir="./logger_output/submitter/",
    ):
        self._data_queue = output_queue
        self._submitter = Submitter(url, log_dir)

    def _submit(self):
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
