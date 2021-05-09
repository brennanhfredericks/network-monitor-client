import argparse
import netifaces
import sys
import queue
import signal
import time
import os
import re
import asyncio
from typing import Optional

from .services import (
    Service_Manager,
    Packet_Parser,
    Interface_Listener,
    Packet_Submitter,
    Packet_Filter,
    Filter,
)


from .protocols import Protocol_Parser
from .configurations import generate_configuration_template, DevConfig, load_config_from_file


async def a_main(interface_name: Optional[str] = None, configuration_file: Optional[str] = None) -> None:

    # load default configuration and override with user values, if any
    app_config: Optional[DevConfig] = None

    # the user can either specify interface or configuration_file
    if interface_name is not None:
        app_config = DevConfig()
        app_config.InterfaceName = interface_name
    elif configuration_file is not None:
        # load file and read data. Override default values with new value
        app_config = load_config_from_file(configuration_file)

    # use config to setup everything

    # interface listener service add raw binary data to queue
    raw_queue: asyncio.Queue = asyncio.Queue()
    # packet parser service consume data from the raw_queue processes the data and adds it to the processed queue
    processed: asyncio.Queue = asyncio.Queue()

    # configure listerner service


async def startup_manager(args) -> None:

    if args.interface or args.load_config_file:

        start_method: Optional[asyncio.Task] = None
        if args.load_config_file:
            if not os.path.exists(args.load_config_file):
                print(f"{args.load_config_file} does not exists")
                sys.exit(1)

            # start from configuration file load
            start_method = asyncio.create_task(a_main(
                configuration_file=args.load_config_file), name="using_configuration_file")

        elif args.interface:
            # start on specified interface
            start_method = asyncio.create_task(
                a_main(interface_name=args.interface), name="using_interfacename")

        # block until done
        await start_method

    else:

        if args.list_gateways:
            print("gateways: ")
            for k, v in netifaces.gateways().items():
                print(f"\taddress family: {k}, interface: {v}")

        if args.list_interfaces:
            print(f"interfaces: {netifaces.interfaces()}")

        if args.generate_config_file:
            generate_configuration_template(args.generate_config_file)
            print("created configuration file")


def args_parser() -> None:

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
    asyncio.run(startup_manager(args))
