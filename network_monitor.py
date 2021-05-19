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
    Interface_Listener,
)
from network_monitor.services import Service_Type, Service_Identifier, Thread_Control, Data_Queue_Identifier
from network_monitor.configurations import DevConfig
from logging import Formatter
from aiologger import Logger
from typing import Optional, Dict, Callable, Awaitable, Coroutine

# execute in its own thread


async def aware_worker(interface_name: str,
                       queue: asyncio.Queue,
                       control: Thread_Control):

    # configure and listerner service
    listener_service: Interface_Listener = Interface_Listener(
        interface_name,
        queue
    )

    out_format = Formatter(
        "%(asctime)s:%(name)s:%(levelname)s"
    )

    logger = Logger.with_default_handlers(
        name="interface_blocking_thread", formatter=None)

    listener_service_task: Task = asyncio.create_task(
        listener_service.worker(logger, control),
        name="listener-service-task"
    )

    await asyncio.gather(listener_service_task, return_exceptions=True)


def blocking_socket(interface_name: str,
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


async def async_ops():
    # before ops that are async
    ...


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

    # # other task list, used to inject asynchruous functionality for blocking code
    # asynchronous_task_list: List[Task] = []

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

    main_loop.add_signal_handler(
        signal.SIGTSTP, functools.partial(signal_handler))
    main_loop.add_signal_handler(
        signal.SIGINT, functools.partial(signal_handler))

    # setup interface thread and controls here
    interface_listener_service_control: Thread_Control = Thread_Control()
    interfac_listener_data_queue: asyncio.Queue = asyncio.Queue()
    interface_listener_service_handler: threading.Thread = threading.Thread(
        group=None,
        target=blocking_socket,
        name="interface-listener-service",
        args=(
            app_config.InterfaceName,
            interfac_listener_data_queue,
            interface_listener_service_control
        ),
        daemon=False
    )
    interface_listener_service_control.handler = interface_listener_service_handler
    services_manager.add_queue(
        interfac_listener_data_queue, Data_Queue_Identifier.Raw_Data)
    services_manager.add_thread(
        "interface_listener_service_thread", interface_listener_service_control)

    asynchronous_service_spawn_task: asyncio.Task = main_loop.create_task(
        async_ops())

    # block until signal shutdown
    while not EXIT_PROGRAM:
        print("main loop - output")
        await services_manager.status()
        await asyncio.sleep(1)

    # cancel all asynchronize service running
    await services_manager.stop_all_services()

    # wait for asynchronous function that spawns asynchronous services
    await asyncio.gather(asynchronous_service_spawn_task)

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
                    start_app(configuration_file=args.load_config_file)
                )

            elif args.interface:
                # start on specified interface
                loop.create_task(
                    start_app(interface_name=args.interface)
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
