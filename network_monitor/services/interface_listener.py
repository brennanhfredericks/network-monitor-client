import ctypes
import socket
import os
import threading
import time
import queue
import sys

# used to manipulate file descriptor for unix
class ifreq(ctypes.Structure):
    _fields_ = [("ifr_ifrn", ctypes.c_char * 16), ("ifr_flags", ctypes.c_short)]


class FLAGS(object):
    # linux/if_ether.h
    ETH_P_ALL = 0x0003  # all protocols
    ETH_P_IP = 0x0800  # IP only
    # linux/if.h
    IFF_PROMISC = 0x100
    # linux/sockios.h
    SIOCGIFFLAGS = 0x8913  # get the active flags
    SIOCSIFFLAGS = 0x8914  # set the active flags


class InterfaceContextManager(object):
    def __init__(self, ifname: str):

        # linux os
        if os.name == "posix":
            import fcntl  # posix-only, use to manipulate file describtor

            # htons: converts 16-bit positive integers from host to network byte order
            sock = socket.socket(
                socket.AF_PACKET, socket.SOCK_RAW, socket.htons(FLAGS.ETH_P_ALL)
            )

            ifr = ifreq()
            # set interface name
            ifr.ifr_ifrn = ifname.encode("utf-8")
            # get active flags for interface
            fcntl.ioctl(sock.fileno(), FLAGS.SIOCGIFFLAGS, ifr)
            # add promiscuous flag
            ifr.ifr_flags |= FLAGS.IFF_PROMISC
            # updated flags
            fcntl.ioctl(sock.fileno(), FLAGS.SIOCSIFFLAGS, ifr)

            # keep a copy of flags state inorder to restore when done
            self._ifr = ifr
        # windows os
        elif os.name == "nt":
            # test to see if working
            self._llsocket.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
            # raise ValueError(f"low level interface for Windows operating system not implemented yet")
        # other os
        else:
            raise ValueError(
                f"low level interface not implemented for {os.name} operating system"
            )

        self._llsocket = sock
        self.hostname = socket.gethostname()

    def __enter__(self):
        return self._llsocket

    def __exit__(self, *exc):
        # linux
        if os.name == "posix":
            import fcntl

            # remove promiscuous flaf
            self._ifr.ifr_flags ^= FLAGS.IFF_PROMISC

            # update interface flags
            fcntl.ioctl(self._llsocket, FLAGS.SIOCSIFFLAGS, self._ifr)
        # windows
        elif os.name == "nt":
            self._llsocket.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)


class Interface_Listener(object):
    # maximum ethernet frame size is 1522 bytes
    BUFFER_SIZE = 65565

    def __init__(self, ifname: str, data_queue: queue.Queue):
        # used to initialize required things

        self.ifname = ifname
        self._data_queue = data_queue

    def _listen(self):
        try:
            with InterfaceContextManager(self.ifname) as interface:
                while self._sentinal:
                    try:
                        # packet = bytes, address
                        packet = interface.recvfrom(self.BUFFER_SIZE)

                        self._data_queue.put(packet)

                    except Exception as e:
                        # add logging functionality here
                        print("listener receiving data from socket {e}")
                        tb = sys.exc_info()
                        print(tb)

                    time.sleep(0.1)

            print("loop stopped")
        except Exception as e:
            self.data_queue.put(e)
            self.data_queue.put(sys.exc_info())

    def stop(self):
        self._sentinal = False
        self._thread_handle.join()

    def start(self):
        self._sentinal = True
        self._thread_handle = threading.Thread(
            target=self._listen, name="network listener", daemon=False
        )
        self._thread_handle.start()
