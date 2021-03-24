import queue
import time
import threading

class Packet_Parser(object):
    def __init__(self, data_queue: queue.Queue, output_queue: queue.Queue = None):

        self.data_queue = data_queue

    def _parser(self):
        
        # clearout data_queue before exiting loop
        while self._sentinal or not self.data_queue.empty():

            if not self.data_queue.empty():
                raw_bytes, address = self.data_queue.get()
                print(address)
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
