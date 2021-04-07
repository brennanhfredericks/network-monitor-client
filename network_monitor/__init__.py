import argparse
import netifaces
import sys
import queue
import signal
import time

from .services import (
    Service_Manager,
    Packet_Parser,
    Interface_Listener,
    Packet_Submitter,
    Packet_Filter,
    Filter,
)

from .configurations import generate_template_configuration


def default_start(args):
    service_manager = None

    if args.interface is not None:

        # check validate choice and start process
        service_manager = Service_Manager(args.interface)
        input_queue = queue.Queue()
        output_queue = queue.Queue()

        # start network listener
        interface_listener = Interface_Listener(args.interface, input_queue)
        service_manager.start_service("interface listener", interface_listener)

        # filter application post request to monitor service
        packet_filter = Packet_Filter()
        # temporary
        packet_filter.register(
            Filter(
                "application submitter service",
                {
                    "IPv4": {
                        "source_address": "127.0.0.1",
                        "destination_address": "127.0.0.1",
                    },
                    "TCP": {
                        "destination_port": 5000,
                    },
                },
            )
        )

        # start packet parser
        packet_parser = Packet_Parser(input_queue, output_queue, packet_filter)
        service_manager.start_service("packet parser", packet_parser)

        # start packet submitter
        packet_submitter = Packet_Submitter(output_queue)
        service_manager.start_service("packet submitter", packet_submitter)

    else:
        if args.list_gateways:
            print("gateways: ")
            for k, v in netifaces.gateways().items():
                print(f"\taddress family: {k}, interface: {v}")

        if args.list_interfaces:
            print(f"interfaces: {netifaces.interfaces()}")

        if args.generate_config_file:
            generate_template_configuration(args.generate_config_file)
            print("created configuration file")

        sys.exit(0)

    # exit cleanly
    def signal_handler(sig, frame):
        service_manager.stop_all_services()
        sys.exit(0)

    signal.signal(signal.SIGTSTP, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # blocking loop
    while True:
        time.sleep(0.05)


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
    basic_parser.add_argument(
        "--generate-config-file",
        action="store",
        type=str,
        help="generate a configuration template file",
    )

    # parse arguments
    args = basic_parser.parse_args()
    default_start(args)
