import netifaces
import argparse


class Service_Manager:
    def __init__(self, interface_name):
        self._ifaddress = netifaces.ifaddresses(interface_name)

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

    if args.interface is not None:
        # check validate choice and start process
        service_manager = Service_Manager(args.interface)
        print(service_manager.interface_addresses)
        print(service_manager.address_family)
        print(service_manager.ipv4_address)
        print(service_manager.ipv6_address)
        print(service_manager.link_layer_address)
    else:

        if args.list_gateways:
            print("gateways: ")
            for k, v in netifaces.gateways().items():
                print(f"\taddress family: {k}, interface: {v}")

        if args.list_interfaces:
            print(f"interfaces: {netifaces.interfaces()}")


if __name__ == "__main__":
    exit(main())