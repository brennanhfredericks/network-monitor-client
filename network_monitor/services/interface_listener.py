import ctypes

import os
import threading
import time
import sys
import asyncio
from socket import socket, AF_PACKET, SOCK_RAW, htons
from asyncio import Queue, CancelledError
from aiologger import Logger
from typing import Optional, List, Dict, Any, Tuple
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
            # test to see if working
            self._llsocket.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
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
            self._llsocket.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)


class Interface_Listener(object):
    # maximum ethernet frame size is 1522 bytes
    BUFFER_SIZE: int = 65565

    def __init__(self, interface_name: str, raw_data_queue: Queue) -> None:
        # used to initialize required things
        # specify the interface to lister on
        self.interface_name: str = interface_name

        # raw ethernet packects put on to queue for processing
        self.raw_data_queue: Queue = raw_data_queue

    async def read(self, interface: socket) -> Tuple[bytes, Tuple[str, int, int, int, bytes]]:

        return interface.recvfrom(self.BUFFER_SIZE)

    # if operation is not suspended or waiting it will pegg processor
    async def worker(self) -> None:

        logger = Logger.with_default_handlers(
            name="interface-listener-service-logger")
        with InterfaceContextManager(self.interface_name) as interface:
            while True:
                s = time.monotonic()
                try:
                    packet: Tuple[bytes, Tuple[str, int, int, int, bytes]] = await self.read(interface)
                    #packet = (5545, 4545454)
                    await asyncio.sleep(0.1)
                    await self.raw_data_queue.put(packet)
                except CancelledError as e:
                    # clean up and re raise to end
                    print("listener service cancelled")
                    raise e

                except Exception as e:
                    # add logging functionality here
                    print("ohter exception: ", e)
                    await logger.exception("listener receiving data from socket {e}")
                print("time diff: ", time.monotonic()-s)
            print("done")
