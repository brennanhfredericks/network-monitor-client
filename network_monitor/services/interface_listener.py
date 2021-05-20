import ctypes

import os

import time
import sys

from socket import socket, AF_PACKET, SOCK_RAW, htons

import logging

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
            ifr.ifr_ifrn = interface_name.encode("utf-8")
            # get active flags for interface
            fcntl.ioctl(sock.fileno(), FLAGS.SIOCGIFFLAGS, ifr)

            # keep a copy of flags state before changing inorder to restore to original state when done
            self._ifr: ifreq = ifr

            # add promiscuous flag
            ifr.ifr_flags |= FLAGS.IFF_PROMISC
            # updated flags
            fcntl.ioctl(sock.fileno(), FLAGS.SIOCSIFFLAGS, ifr)

        # windows os
        elif os.name == "nt":
            raise NotImplemented
            # test to see if working
            # self._llsocket.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
            # raise ValueError(f"low level interface for Windows operating system not implemented yet")
        # other os
        else:
            raise ValueError(
                f"low level interface not implemented for {os.name} operating system"
            )

        self._llsocket: socket = sock

    def __enter__(self) -> socket:
        return self._llsocket

    def __exit__(self, *exc) -> None:
        # linux
        if os.name == "posix":
            import fcntl

            # remove promiscuous flaf
            self._ifr.ifr_flags ^= FLAGS.IFF_PROMISC

            # update interface flags
            fcntl.ioctl(self._llsocket, FLAGS.SIOCSIFFLAGS, self._ifr)
        # windows
        elif os.name == "nt":
            # self._llsocket.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
            ...


class Interface_Listener(object):
    # maximum ethernet frame size is 1522 bytes
    BUFFER_SIZE: int = 65565

    def __init__(self, interface_name: str, log_directory: str) -> None:
        # used to initialize required things
        # specify the interface to lister on
        self.interface_name: str = interface_name

    # if operation is not true asynchronous hence the need to run in a seperate thread
    def worker(self, service_control: Service_Control) -> None:

        stream_format = logging.Formatter(
            "%(asctime)s -:- %(name)s -:- %(levelname)s -:- %(message)s"
        )

        # configure logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        # add stream handler
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(stream_format)
        logger.addHandler(stream_handler)

        file_handler = logging.FileHandler(
            filename=f"./logs/Logging/interface_listener.log")
        logger.addHandler(file_handler)

        # try to open low level socket
        try:

            with InterfaceContextManager(self.interface_name) as interface:
                # no error occured
                service_control.error = False

                while service_control.sentinal:
                    # s = time.monotonic()
                    try:
                        #
                        packet: Tuple[bytes, Tuple[str, int, int, int, bytes]] = interface.recvfrom(
                            self.BUFFER_SIZE)
                        # time the packed got sniffed
                        sniffed_timestamp: float = time.time()

                        # add raw to be processed by other service
                        service_control.out_queue.put(
                            (sniffed_timestamp, packet)
                        )

                    except Exception:
                        logger.exception(
                            f"An exception occured trying to read data from {self.interface_name}")

        except Exception:
            service_control.error = True

            logger.exception(
                f"An exception occured opening a low level socket")

        # thread exit normally
