import netifaces
import argparse
import collections
import time
import signal
import sys

# services
from interface_listener import Network_Listener


class Service_Manager(object):
    def __init__(self, interface_name):
        self._ifname = interface_name
        self._ifaddress = netifaces.ifaddresses(interface_name)
        self._services = collections.OrderedDict()

    @property
    def interface_addresses(self):
        return self._ifaddress

    @property
    def address_family(self):
        return list(self._ifaddress.keys())

    @property
    def ipv4_address(self):

        if netifaces.AF_INET in self._ifaddress.keys():
            return self._ifaddress[netifaces.AF_INET]

        return None

    @property
    def ipv6_address(self):

        if netifaces.AF_INET6 in self._ifaddress.keys():
            return self._ifaddress[netifaces.AF_INET6]

        return None

    @property
    def link_layer_address(self):

        if netifaces.AF_LINK in self._ifaddress.keys():
            return self._ifaddress[netifaces.AF_LINK]

        return None
    def start(self):
        # use to start service in the correct order
        
        # network listining service
        network_listener = Network_Listener(self._ifname)

        self._start_service("network listener",network_listener)

    def stop (self):
        # use to stop service in the correct order
        # need to stop service using signal, check to handle exit case correctly
        
        self._stop_all_services()

    def _start_service(self,service_name:str,service_obj):
        # start service
        service_obj.start()
        
        # add service to Order dict
        self._services[service_name] = service_obj

    def _stop_all_services(self):
        
        for k,v in self._services.items():
            #stop service and join thread
            v.stop()
            print(f"{k} service stopped")

        self._services.clear()

def main():

    basic_parser = argparse.ArgumentParser(
        description="monitor ethernet network packets.", add_help=True
    )

    # add arguments
    basic_parser.add_argument(
        "-i",
        "--interface",
        action="store",
        choices=netifaces.interfaces(),
        type=str,
        help="specify which interface to monitor",
    )
    basic_parser.add_argument(
        "-li",
        "--list-interfaces",
        action="store_true",
        help="list all available interfaces",
    )
    basic_parser.add_argument(
        "-lg",
        "--list-gateways",
        action="store_true",
        help="list all available gateways",
    )

    # parse arguments
    args = basic_parser.parse_args()
    service_manager = None
    if args.interface is not None:
        # check validate choice and start process
        service_manager = Service_Manager(args.interface)
        
        service_manager.start()
        #time.sleep(5)
        #service_manager.stop()

    else:

        if args.list_gateways:
            print("gateways: ")
            for k, v in netifaces.gateways().items():
                print(f"\taddress family: {k}, interface: {v}")

        if args.list_interfaces:
            print(f"interfaces: {netifaces.interfaces()}")

        sys.exit(0)
    # need to block in def, fix ctrl -z issue

    def signal_handler(sig, frame):
        print('You pressed Ctrl+C! or Ctrl+Z!')
        service_manager.stop()
        sys.exit(0)

    signal.signal(signal.SIGTSTP, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    while True:
            time.sleep(0.1)


if __name__ == "__main__":
    exit(main())