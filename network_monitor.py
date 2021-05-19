import netifaces
import argparse
import asyncio
import os
import signal
import functools
import threading
from asyncio import Task
from network_monitor import (
    generate_configuration_template,
    load_config_from_file,
    Service_Manager,
)
from network_monitor.services import (
    Service_Type,
    Service_Identifier,
    Thread_Control,
    Data_Queue_Identifier,
    Interface_Listener,
    Packet_Parser,
    Packet_Submitter,
    Packet_Filter
)
from network_monitor.configurations import DevConfig

from network_monitor.protocols import Protocol_Parser
from logging import Formatter
from aiologger import Logger
from typing import Optional, Dict, Callable, Awaitable, Coroutine

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

    loop.create_task(
        listener_service.worker(control),
        name="listener-service-task"
    )

    # use introspection to retrieve all task

    tasks = asyncio.all_tasks(loop=loop)

    await asyncio.gather(*tasks, return_exceptions=False)


def threaded_event_loop(interface_name: str,
                        queue: asyncio.Queue,
                        control: Thread_Control):

    # create a new event loop and add the interfce listener service to the loop.
    # the service is async aware however still operation in a blocking manner

    # can always later use new eventloop to peform other corotines.
    # could also use introspection to gather current task or all tasks in provided loop
    # asyncio.run_coroutine_threadsafe to add corotines between threads
    asyncio.run(
        aware_worker(
            interface_name, queue, control)
    )


async def init_blocking_services(app_config: DevConfig, services_manager: Service_Manager) -> None:
    # setup service control mechanicm
    interface_listener_service_control: Thread_Control = Thread_Control()

    # configure service thread
    interface_listener_service_control.handler = threading.Thread(
        group=None,
        target=threaded_event_loop,
        name="interface-listener-service",
        args=(
            app_config.InterfaceName,
            services_manager.get_queue(Data_Queue_Identifier.Raw_Data),
            interface_listener_service_control
        ),
        daemon=False
    )

    # add thread to services manager and start
    services_manager.add_thread(
        "interface-listener-service", interface_listener_service_control)

    # wait a moment to check if service started in thread
    await asyncio.sleep(0.1)

    # check  if any error occured
    if interface_listener_service_control.error_state:
        print("error occured in thread")
        # stop the thread that the error occured in
        services_manager.stop_thread("interface-listener-service")

        # for now force application to exit by throwing and exception. this exeception in captured in the main function.
        # raise ValueError(
        #     "Unable to start interface listener most likely due to insufficient privileges")


async def init_asynchronous_services(app_config: DevConfig, services_manager: Service_Manager) -> None:
    # before ops that are asynchronize , running in main loop
    loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
    # packet parser service consume data from the raw_queue processes the data and adds it to the processed queue

    # configure logger and output directory Protocol Parser
    Protocol_Parser.set_output_directory(app_config.undefined_storage_path())
    Protocol_Parser.set_async_loop(loop)

    # configure packet filter. Need implement FilterSubmissionTraffic, only a issue if the application network packets need to be routed via
    # the listening interface to reach the monitor server.

    # create a new Packet_Filter. The Packet_Filter holds all filters and applies them to the captured packets
    packet_filter: Packet_Filter = Packet_Filter(
        app_config.FilterSubmissionTraffic)

    # register all filters define in the configuration file
    packet_filter.register(app_config.Filters)

    # configure packet parser service
    packet_parser: Packet_Parser = Packet_Parser(
        services_manager.get_queue(Data_Queue_Identifier.Raw_Data), services_manager.get_queue(Data_Queue_Identifier.Processed_Data), packet_filter)

    # create asynchronous service task
    packet_parser_service_task: Task = asyncio.create_task(
        packet_parser.worker(), name="packet-parser-service-task")

    # create reference - consumes and produces data
    services_manager.add_service(
        Service_Type.Consumer, Service_Identifier.Packet_Parser_Service, packet_parser_service_task)

    # configure packet submitter service
    packet_submitter: Packet_Submitter = Packet_Submitter(
        services_manager.get_queue(Data_Queue_Identifier.Processed_Data),
        app_config.RemoteMetadataStorage,
        app_config.local_metadata_storage_path(),
        app_config.ResubmissionInterval
    )

    packet_submitter_service_task: Task = asyncio.create_task(
        packet_submitter.worker(), name="packet=submitter-service-task"
    )

    services_manager.add_service(
        Service_Type.Consumer, Service_Identifier.Packet_Submitter_Service, packet_submitter_service_task)


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

    # main loop blocking part
    EXIT_PROGRAM: bool = False

    def signal_handler(*args):
        # use parent scope variable
        nonlocal EXIT_PROGRAM
        print("application starting exist process")
        # stop threads, only have one producer thread for now.
        services_manager.stop_threads()
        print("all threads have been stopped")
        # change blocking loop control
        EXIT_PROGRAM = True

    # ctrl+z and ctrl+c signal handlers
    main_loop.add_signal_handler(
        signal.SIGTSTP, functools.partial(signal_handler))
    main_loop.add_signal_handler(
        signal.SIGINT, functools.partial(signal_handler))

    # configure data queues
    raw_queue: asyncio.Queue = asyncio.Queue()
    processed_queue: asyncio.Queue = asyncio.Queue()

    services_manager.add_queue(
        raw_queue, Data_Queue_Identifier.Raw_Data)
    services_manager.add_queue(
        processed_queue, Data_Queue_Identifier.Processed_Data)

    # wait for producer service to start before trying to start any consumer services
    await main_loop.create_task(init_blocking_services(app_config, services_manager))

    main_loop.create_task(
        init_asynchronous_services(app_config, services_manager))

    # block until signal shutdown
    while not EXIT_PROGRAM:
        print("main loop - output")
        await services_manager.status()
        await asyncio.sleep(1)

    # cancel all asynchronize service running
    await services_manager.stop_all_services()

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
