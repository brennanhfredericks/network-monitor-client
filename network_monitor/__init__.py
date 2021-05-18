import argparse
import netifaces
import sys

import signal
import time
import os
import asyncio


from asyncio import CancelledError, Task
from typing import Optional, List, Any

from .services import (
    Service_Manager,
    Packet_Parser,
    Interface_Listener,
    Packet_Submitter,
    Packet_Filter,
    Filter,
    Service_Type,
    Service_Identifier,
    Data_Queue_Identifier
)

from logging import Formatter
from aiologger import Logger

from .protocols import Protocol_Parser
from .configurations import generate_configuration_template, DevConfig, load_config_from_file


async def start_services(app_config: Optional[DevConfig], services_manager: Service_Manager, asynchronous_task_list: List[Task], ):
    # use config to setup everything
    # interface listener service add raw binary data to queue
    raw_queue: asyncio.Queue = asyncio.Queue()

    services_manager.add_queue(raw_queue, Data_Queue_Identifier.Raw_Data)
    # packet parser service consume data from the raw_queue processes the data and adds it to the processed queue
    processed_queue: asyncio.Queue = asyncio.Queue()

    services_manager.add_queue(
        processed_queue, Data_Queue_Identifier.Processed_Data)

    # setup logger
    # gbl_format = Formatter(
    #     "%(asctime)s %(levelname)s %(message)s %(funcName)s")
    logger = Logger.with_default_handlers()

    # configure logger and output directory Protocol Parser
    await Protocol_Parser.init_asynchronous_operation(app_config.undefined_storage_path(), logger, asynchronous_task_list)

    # configure and listerner service
    listener_service: Interface_Listener = Interface_Listener(
        app_config.InterfaceName, raw_queue)

    listener_service_task: Task = asyncio.create_task(
        listener_service.worker(logger), name="listener-service-task")

    services_manager.add_service(
        Service_Type.Producer, Service_Identifier.Interface_Listener_Service, listener_service_task)

    # configure packet parser
    packet_filter: Packet_Filter = Packet_Filter(
        app_config.FilterSubmissionTraffic)

    packet_filter.register(app_config.Filters)
    packer_parser: Packet_Parser = Packet_Parser(
        raw_queue, processed_queue, packet_filter)

    packet_parser_service_task: Task = asyncio.create_task(
        packer_parser.worker(logger), name="packet-parser-service-task")

    # produces and consumes data
    services_manager.add_service(
        Service_Type.Consumer, Service_Identifier.Packet_Parser_Service, packet_parser_service_task)

    # configure submitter service
    packet_submitter: Packet_Submitter = Packet_Submitter(
        processed_queue,
        app_config.RemoteMetadataStorage,
        app_config.local_metadata_storage_path(),
        app_config.ResubmissionInterval
    )

    packet_submitter_service_task: Task = asyncio.create_task(
        packet_submitter.worker(logger))

    services_manager.add_service(
        Service_Type.Consumer, Service_Identifier.Packet_Submitter_Service, packet_submitter_service_task)


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

    # other task list, used to inject asynchruous functionality for blocking code
    asynchronous_task_list: List[Task] = []

    # holds all coroutine services
    services_manager: Service_Manager = Service_Manager()

    # test only

    await start_services(app_config, services_manager, asynchronous_task_list)

    loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
    EXIT_PROGRAM: bool = False

    def signal_handler(*args):
        # use parent scope variable
        nonlocal EXIT_PROGRAM
        EXIT_PROGRAM = True

    signal.signal(signal.SIGTSTP, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # block until signal shutdown
    while not EXIT_PROGRAM:
        await services_manager.status()
        await asyncio.sleep(30)

    await services_manager.stop_all_services()
    await asyncio.gather(*asynchronous_task_list, return_exceptions=True)


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
        await asyncio.gather(start_method, return_exceptions=False)

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
    asyncio.run(startup_manager(args), debug=False)
