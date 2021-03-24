import ctypes
import socket
import os

# used to manipulate file descriptor for unix
class ifreq(ctypes.Structure):
    _fields_ = [("ifr_ifrn", ctypes.c_char * 16), ("ifr_flags", ctypes.c_short)]


class FLAGS:
    # linux/if_ether.h
    ETH_P_ALL = 0x0003  # all protocols
    ETH_P_IP = 0x0800  # IP only
    # linux/if.h
    IFF_PROMISC = 0x100
    # linux/sockios.h
    SIOCGIFFLAGS = 0x8913  # get the active flags
    SIOCSIFFLAGS = 0x8914  # set the active flags

class InterfaceContextManager():

    def __init__(self,interface_name):

        # linux os
        if os.name = 'posix':
            import fcntl # posix-only, use to manipulate file describtor
            
            # htons: converts 16-bit positive integers from host to network byte order
            sock = socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.htons(FLAGS.ETH_P_ALL))

            ifr = ifreq()
            # set interface name
            ifr.ifr_ifrn = interface_name.encode('utf-8')
            # get active flags for interface
            fcntl.ioctl(sock.fileno(),FLAGS.SIOCGIFFLAGS,ifr)
            # add promiscuous flag
            ifr.ifr_flags |= FLAGS.IFF_PROMISC
            # updated flags
            fcntl.ioctl(sock.fileno(),FLAGS.SIOCSIFFLAGS,ifr)

            # keep a copy of flags state inorder to restore when done
            self._ifr = ifr
        # windows os
        elif os.name = 'nt':
            # test to see if working
            self._llsocket.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
            #raise ValueError(f"low level interface for Windows operating system not implemented yet")
        # other os
        else:
            raise ValueError(f"low level interface not implemented for {os.name} operating system")
        
        self._llsocket = sock
        self.hostname = socket.gethostname()

    def __enter__(self):
        return self._llsocket

    def __exit__(self):
        # linux
        if os.name == 'posix':
            import fcntl
            # remove promiscuous flaf
            self._ifr.ifr_flags ^= FLAGS.IFF_PROMISC

            # update interface flags
            fcntl.ioctl(self._llsocket,FLAGS.SIOCSIFFLAGS,self._ifr)
        # windows
        elif os.name == 'nt':
            self._llsocket.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)


        