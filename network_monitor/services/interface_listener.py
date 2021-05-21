import ctypes

import os
import fcntl
import time
import sys

from socket import socket, AF_PACKET, SOCK_RAW, htons

from aiologger import Logger
from aiologger.handlers.files import AsyncFileHandler
from aiologger.handlers.streams import AsyncStreamHandler


from typing import List, Any, Tuple
from .service_manager import Service_Control

# used to manipulate file descriptor for unix


class ifreq(ctypes.Structure):
    _fields_: List[Tuple[str, Any]] = [("ifr_ifrn", ctypes.c_char * 16),
                                       ("ifr_flags", ctypes.c_short)]


class FLAGS(object):
    # linux/if_ether.h
    ETH_P_ALL: int = 0x0003  # all protocols
    ETH_P_IP: int = 0x0800  # IP only
    # linux/if.h
    IFF_PROMISC: int = 0x100
    # linux/sockios.h
    SIOCGIFFLAGS: int = 0x8913  # get the active flags
    SIOCSIFFLAGS: int = 0x8914  # set the active flags


class InterfaceContextManager(object):
    """
        abstraction layer for different operating systems. only tested ubuntu linux
    """

    def __init__(self, interface_name: str) -> None:
        self.interface_name = interface_name

    def get_socket(self) -> socket:
        # linux os
        if os.name == "posix":
            import fcntl  # posix-only, use to manipulate file describtor

            # htons: converts 16-bit positive integers from host to network byte order
            sock: socket = socket(
                AF_PACKET, SOCK_RAW, htons(
                    FLAGS.ETH_P_ALL)
            )
            # sock.setblocking(False)
            ifr: ifreq = ifreq()
            # set interface name
            ifr.ifr_ifrn = self.interface_name.encode("utf-8")
            # get active flags for interface
            fcntl.ioctl(sock.fileno(), FLAGS.SIOCGIFFLAGS, ifr)

            # keep a copy of flags state before changing inorder to restore to original state when done
            self._ifr: ifreq = ifr

            # add promiscuous flag
            ifr.ifr_flags |= FLAGS.IFF_PROMISC
            # updated flags
            fcntl.ioctl(sock.fileno(), FLAGS.SIOCSIFFLAGS, ifr)
        else:
            raise ValueError("posix only")

        self._llsocket: socket = sock
        return self._llsocket

    def close(self) -> None:
        # linux
        # remove promiscuous flaf
        self._ifr.ifr_flags ^= FLAGS.IFF_PROMISC
        # update interface flags
        fcntl.ioctl(self._llsocket, FLAGS.SIOCSIFFLAGS, self._ifr)
        self._llsocket.close()

    def __enter__(self) -> socket:
        return self._llsocket

    def __exit__(self, *exc) -> None:
        self.close()


class Interface_Listener(object):
    # maximum ethernet frame size is 1522 bytes
    BUFFER_SIZE: int = 65565

    def __init__(self, interface_name: str, log_directory: str) -> None:
        # used to initialize required things
        # specify the interface to lister on
        self.interface_name: str = interface_name
        self.log_directory: str = log_directory

    # if operation is not true asynchronous hence the need to run in a seperate thread
    async def worker(self, service_control: Service_Control) -> None:
        # configure logger
        logger = Logger(name=__name__)

        # add stream handler
        stream_handler = AsyncStreamHandler(stream=sys.stderr)
        logger.add_handler(stream_handler)

        try:
            file_handler = AsyncFileHandler(
                filename=os.path.join(self.log_directory, "interface_listener.log"))
            logger.add_handler(file_handler)
        except Exception as e:
            # permission error
            service_control.error = True
            await logger.exception(
                f"Unable to create log file for interface listener service: {e}")
            return

        # try to open low level socket
        try:
            icm = InterfaceContextManager(
                self.interface_name
            )
            pm_socket = icm.get_socket()

        except Exception as e:
            service_control.error = True
            await logger.exception(
                f"Unable open a low level socket: {e}"
            )

        else:
            service_control.error = False

            while service_control.sentinal:
                # s = time.monotonic()
                try:
                    #
                    packet: Tuple[bytes, Tuple[str, int, int, int, bytes]] = pm_socket.recvfrom(
                        self.BUFFER_SIZE)
                    # time the packed got sniffed
                    sniffed_timestamp: float = time.time()

                    # add raw to be processed by other service
                    await service_control.out_queue.put(
                        (sniffed_timestamp, packet)
                    )

                except Exception:
                    await logger.exception(
                        f"An exception occured trying to read data from {self.interface_name}")
        finally:

            if not service_control.error:
                pm_socket.close()
