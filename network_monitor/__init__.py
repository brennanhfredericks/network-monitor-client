import argparse
import netifaces
import sys
import queue
import signal
import time
import os
import configparser
import re
from .services import (
    Service_Manager,
    Packet_Parser,
    Interface_Listener,
    Packet_Submitter,
    Packet_Filter,
    Filter,
)
from .protocols import Protocol_Parser
from .configurations import generate_template_configuration


def startup_manager(args):

    if args.interface or args.load_config_file:

        if args.load_config_file:
            if not os.path.exists(args.load_config_file):
                print(f"{args.load_config_file} does not exists")
                sys.exit(1)

            # start from configuration file load
            start_from_configuration_file(args.load_config_file)
        elif args.interface:
            # start on specified interface
            default_start_on_interface(args.interface)
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


def start_from_configuration_file(config_path: str):

    config = configparser.ConfigParser()

    res = config.read(config_path)

    if len(res) == 0:
        print(f"Unsuccessfull at parsing {config_path}")
        sys.exit(1)

    # check if interface name is provide and is valid
    ifname = config.get("ListenerService", "InterfaceName", fallback=None)
    if ifname is None:
        print(f"InterfaceName is not specified")
        sys.exit(1)
    else:
        if ifname not in netifaces.interfaces():
            print(f"{ifname} is not a valid interface")
            sys.exit(1)

    # application log directory
    log = config.get("Application", "Log", fallback="./logs/application/general")

    # unknown protocols log directory
    unknownprotocols = config.get(
        "Application",
        "UnknownProtocols",
        fallback="./logs/application/unknown_protocols",
    )

    # filter all traffic generated by application
    filterallapplicationtraffic = config.get(
        "Application", "FilterAllApplicationTraffic", fallback=False
    )

    # local directory to store packets when monitor server unavailable
    local = config.get(
        "SubmitterService", "Local", fallback="./logs/submitter_service/"
    )

    # url for monitor server, where packets are submitted
    url = config.get(
        "SubmitterService", "Url", fallback="http://127.0.0.1:5000/packets"
    )

    # timeout for resubmission of logged data
    retryinterval = config.get("SubmitterService", "RetyInterval", fallback=300)

    # retrieve filters
    filters = [re.search("Filter", section) for section in config.sections()]
    collect_filters = []
    for idx, filtr in enumerate(filters):

        if filtr is None:
            continue

        section = config.sections()[idx]

        def_ = config.get(section, "Definition", fallback=None)

        if def_ is not None:
            try:
                def_filter = Filter(section, def_)
            except Exception as e:
                print(f"issue with {section}: {e}")
                sys.exit(1)
            else:
                collect_filters.append(def_filter)

    if not collect_filters:
        ## check for default filter
        if "filter" in config.defaults():

            filtr = config.defaults()["filter"]
            try:
                def_filter = Filter("default", filtr)
            except Exception as e:
                print(f"issue with default filter: {e}")
                sys.exit(1)
            else:
                collect_filters.append(def_filter)

    # parser output directory
    Protocol_Parser.set_log_directory(unknownprotocols)

    # check validate choice and start process
    service_manager = Service_Manager(ifname)
    input_queue = queue.Queue()
    output_queue = queue.Queue()

    # start network listener
    interface_listener = Interface_Listener(ifname, input_queue)
    service_manager.start_service("interface listener", interface_listener)

    # filter application post request to monitor service
    packet_filter = Packet_Filter(
        filter_application_packets=filterallapplicationtraffic
    )

    # regiter filters
    packet_filter.register(collect_filters)

    # start packet parser
    packet_parser = Packet_Parser(input_queue, output_queue, packet_filter)
    service_manager.start_service("packet parser", packet_parser)

    # start packet submitter
    packet_submitter = Packet_Submitter(output_queue, url, local, retryinterval)
    service_manager.start_service("packet submitter", packet_submitter)

    # exit cleanly
    def signal_handler(sig, frame):
        service_manager.stop_all_services()
        sys.exit(0)

    signal.signal(signal.SIGTSTP, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # blocking loop
    while True:
        time.sleep(0.05)


def default_start_on_interface(ifname: str):

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
        "-gcf",
        "--generate-config-file",
        action="store",
        type=str,
        help="generate a configuration template file",
    )
    basic_parser.add_argument(
        "-lcf",
        "--load-config-file",
        action="store",
        type=str,
        help="load a configuration file",
    )

    # parse arguments
    args = basic_parser.parse_args()
    startup_manager(args)
