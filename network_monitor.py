from typing import Optional, Dict, Callable, Awaitable, Coroutine, List
from aiologger import Logger
from logging import Formatter
from network_monitor.protocols import Protocol_Parser
from network_monitor.configurations import DevConfig
from network_monitor.services import (
    Service_Type,
    Service_Identifier,
    Service_Control,
    Data_Queue_Identifier,
    Interface_Listener,
    Packet_Parser,
    Packet_Submitter,
    Packet_Filter
)
from network_monitor import (
    generate_configuration_template,
    load_config_from_file,
    Service_Manager,
)
import netifaces
import argparse
import asyncio
import os
import signal
import functools
import threading
import queue
import logging


# execute in its own thread


async def aware_worker(interface_name: str,
                       queue: asyncio.Queue,
                       control: Thread_Control):

    loop = asyncio.get_running_loop()

    # set refence to this loop, could always push corotine to this loop aswell
    control.loop = loop

    # configure and listerner service
    listener_service: Interface_Listener = Interface_Listener(
        interface_name,
        queue
    )

    listener_service_task = loop.create_task(
        listener_service.worker(control),
        name="listener-service-task"
    )

    await asyncio.gather(listener_service_task, return_exceptions=False)


def threaded_packet_submitter_service(services_manager: Service_Manager, service_control: Service_Control, **kwargs) -> threading.Thread:

    # retrieve args
    remote_metadata_storage: str = kwargs.pop("RemoteMetadataStorage")
    local_metadata_storage: str = kwargs.pop("LocalMetadataStorage")
    resubmission_interval: int = kwargs.pop("ResubmissionInterval")
    # configure packet submitter service
    packet_submitter: Packet_Submitter = Packet_Submitter(
        services_manager.get_queue(Data_Queue_Identifier.Processed_Data),
        remote_metadata_storage,
        local_metadata_storage,
        resubmission_interval
    )

    packet_submitter_service_task: asyncio.Task = asyncio.create_task(
        packet_submitter.worker(), name="packet=submitter-service-task"
    )

    services_manager.add_service(
        Service_Type.Consumer, Service_Identifier.Packet_Submitter_Service, packet_submitter_service_task)


def threaded_interface_listener_service(services_manager: Service_Manager, service_control: Service_Control, **kwargs) -> threading.Thread:

    # retrieve kwargs
    interface_name = kwargs.pop("InterfaceName")
    log_directory = kwargs.pop("LogDirectory")

    # configure interface and log directory for interface listener
    interface_listener: Interface_Listener = Interface_Listener(
        interface_name,
        log_directory
    )

    # configure interface listener output queue
    service_control.out_queue = queue.Queue()

    # configure service thread
    service_control.thread = threading.Thread(
        group=None,
        target=interface_listener.worker,
        name="interface-listener-service",
        args=(
            service_control,
        ),
        daemon=False
    )

    # add thread to services manager and start
    services_manager.add_thread(
        "interface-listener-service", service_control)


async def app_status(services_manager: Service_Manager, update_interval: int = 5):
    while services_manager.run:
        print("main loop - output")
        await services_manager.status()
        await asyncio.sleep(update_interval)
        # cancel all asynchronize service running
    await services_manager.stop_all_services()


async def asynchronous_packet_parser_service(service_control: Service_Control, **kwargs) -> asyncio.Task:
    # configure packet filter. Need implement FilterSubmissionTraffic, only a issue if the application network packets need to be routed via
    # the listening interface to reach the monitor server.
    filter_submission_traffic = kwargs.pop("FilterSubmissionTraffic")
    filters = kwargs.pop("Filters")

    # create a new Packet_Filter. The Packet_Filter holds all filters and applies them to the captured packets
    packet_filter: Packet_Filter = Packet_Filter(
        filter_submission_traffic)

    # register all filters define in the configuration file
    packet_filter.register(filters)

    service_control.out_queue = queue.Q

    # configure packet parser service
    packet_parser: Packet_Parser = Packet_Parser(
        services_manager.get_queue(Data_Queue_Identifier.Raw_Data), services_manager.get_queue(Data_Queue_Identifier.Processed_Data), packet_filter)

    # create asynchronous service task
    packet_parser_service_task: asyncio.Task = asyncio.create_task(
        packet_parser.worker(), name="packet-parser-service-task")

    # create reference - consumes and produces data
    services_manager.add_service(
        Service_Type.Consumer, Service_Identifier.Packet_Parser_Service, packet_parser_service_task)


async def start_app(interface_name: Optional[str] = None, configuration_file: Optional[str] = None) -> None:

    # get main asyncio loop
    main_loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()

    # parse configuration
    # load default configuration and override with user values, if any
    app_config: Optional[DevConfig] = None

    # the user can either specify interface or configuration_file
    if interface_name is not None:
        app_config = DevConfig()
        app_config.InterfaceName = interface_name
    elif configuration_file is not None:
        # load file and read data. Override default values with new value
        app_config = load_config_from_file(configuration_file)

    # # holds all coroutine services
    services_manager: Service_Manager = Service_Manager()

    def signal_handler(*args):
        # use parent scope variable
        print("application starting exist process")
        # stop threads, only have one producer thread for now.
        services_manager.stop_threads()
        print("all threads have been stopped")
        # change blocking loop control
        services_manager.run = False

    # ctrl+z and ctrl+c signal handlers
    main_loop.add_signal_handler(
        signal.SIGTSTP, functools.partial(signal_handler))
    main_loop.add_signal_handler(
        signal.SIGINT, functools.partial(signal_handler))

    # configure data queues
    # raw_queue: asyncio.Queue = asyncio.Queue()
    # processed_queue: asyncio.Queue = asyncio.Queue()

    # services_manager.add_queue(
    #     raw_queue, Data_Queue_Identifier.Raw_Data)
    # services_manager.add_queue(
    #     processed_queue, Data_Queue_Identifier.Processed_Data)

    # wait for producer service to start before trying to start any consumer services
    await main_loop.create_task(init_blocking_services(app_config, services_manager))

    # configure logger and output directory Protocol Parser
    Protocol_Parser.set_output_directory(app_config.undefined_storage_path())
    Protocol_Parser.set_async_loop(main_loop)

    packet_parser_service_task = await main_loop.create_task(
        packet_parser_service(app_config, services_manager))

    packet_submitter_service_task = await main_loop.create_task(
        packet_submitter_service(app_config, services_manager))

    services_manager.run = True
    app_status_task: asyncio.Task = main_loop.create_task(
        app_status(services_manager))
    # block until signal shutdown

    await asyncio.gather(app_status_task, packet_parser_service_task, packet_submitter_service_task, return_exceptions=True)

    # use introspection to retrieve all set of not yet finished Task objects run by the loop.
    if len(asyncio.all_tasks(main_loop)) > 1:
        # wait for other tasks to complete
        tasks = []
        for task in asyncio.all_tasks(main_loop):
            # skip this coroutine function
            if task.get_coro().__name__ == "start_app":
                continue
            tasks.append(task)
        # error out on exceptions
        await asyncio.gather(*tasks, return_exceptions=False)
        main_loop.stop()
    else:
        # stop main loop
        main_loop.stop()


def main(args: argparse.Namespace) -> int:

    # first do info args before starting application
    if args.list_gateways:
        print("gateways: ")
        for k, v in netifaces.gateways().items():
            print(f"\taddress family: {k}, interface: {v}")

    if args.list_interfaces:
        print(f"interfaces: {netifaces.interfaces()}")

    if args.generate_config_file:
        generate_configuration_template(args.generate_config_file)
        print(f"created configuration file: {args.generate_config_file}")

    # start application
    if args.interface or args.load_config_file:
        # app initiate method

        try:
            loop = asyncio.get_event_loop()
        except Exception as e:
            print(f"An error occurred when trying to start application: {e}")
            return 1
        else:
            #init_method: Optional[asyncio.Task] = None
            if args.load_config_file:
                if not os.path.exists(args.load_config_file):
                    print(f"{args.load_config_file} does not exists")
                    # exit failure
                    return 1

                # init_method from configuration file load
                loop.create_task(
                    start_app(configuration_file=args.load_config_file),
                    name="start_app"
                )

            elif args.interface:
                # start on specified interface
                loop.create_task(
                    start_app(interface_name=args.interface),
                    name="start_app"
                )

            # run until loop.stop() is call
            loop.run_forever()
        finally:
            loop.close()
            # flush out all logger handles
            logging.shutdown()
            print("application closed")
    # exit_succes
    return 0


def args_parser() -> int:

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
    args: argparse.Namespace = basic_parser.parse_args()

    return main(args)


if __name__ == "__main__":

    exit(args_parser())
