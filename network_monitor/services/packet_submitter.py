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

    def __init__(
        self, url: str, log_dir, max_buffer_size: int = 50, re_try_interval=60 * 5
    ):

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

        self.max_buffer_size = max_buffer_size
        self.__buffer_writes = 0
        self.__buffer = StringIO()

    # submit data to server asynchronously
    def submit(self, data):
        post_success = False
        # try post quest
        try:
            r = requests.post(self._url, data=data, timeout=0.001)
        except Exception as e:
            # print(e)
            ...
        else:
            if r.status_code == 200:
                post_success = True

        if not post_success:

            self._log(data)

    # clear buffer and write data to file
    def _clear_buffer(self):

        with open(self.out_file, "a") as fout:

            fout.write(self.__buffer.getvalue())

        self.__buffer.close()
        self.__buffer = StringIO()
        self.__buffer_writes = 0

    # write data to buffer
    def _log(self, data):

        _out = base64.b64encode(data).decode("utf-8")
        self.__buffer.write(_out + "\n")
        self.__buffer_writes += 1

        if self.__buffer_writes > self.max_buffer_size:
            # clear buffer to file append
            self._clear_buffer()


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
                data = {}
                for f in f_protocols:
                    data[f.identifier] = f.serialize()

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
