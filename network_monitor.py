import netifaces
import argparse
import asyncio
import os
import signal
import functools
import concurrent.futures
from asyncio import Task
from network_monitor import (
    generate_configuration_template,
    load_config_from_file,
    Service_Manager,
    Data_Queue_Identifier,
    Interface_Listener,
    Service_Type,
    Service_Identifier,
)
from network_monitor.configurations import DevConfig
from logging import Formatter
from aiologger import Logger
from typing import Optional, Dict, Callable, Awaitable

# execute in its own thread

# calling async aware function, however still blocking


async def blocking_socket(interface_name: str,
                          register_queue: Callable[[asyncio.Queue, Data_Queue_Identifier], None],
                          register_service: Callable[[Service_Type, Service_Identifier, asyncio.Task], None]):
    blocking_loop = asyncio.new_event_loop()
    out_format = Formatter(
        "%(asctime)s:%(name)s:%(levelname)s:%(message)s"
    )
    queue: asyncio.Queue = asyncio.Queue()
    logger = Logger.with_default_handlers(
        name="interface_blocking_thread", formatter=out_format)

    # configure and listerner service
    listener_service: Interface_Listener = Interface_Listener(
        interface_name,
        queue
    )

    listener_service_task: Task = blocking_loop.create_task(
        listener_service.worker(logger),
        name="listener-service-task"
    )

    register_queue(queue, Data_Queue_Identifier)
    register_service(Service_Type.Producer,
                     Service_Identifier.Interface_Listener_Service, listener_service_task)

    await asyncio.gather(listener_service_task, return_exceptions=True)


async def async_ops():
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
        # change end blocking loop
        EXIT_PROGRAM = True

    main_loop.add_signal_handler(
        signal.SIGTSTP, functools.partial(signal_handler))
    main_loop.add_signal_handler(
        signal.SIGINT, functools.partial(signal_handler))

    # await main_loop.create_task(asyncio.sleep(5))

    executer: concurrent.futures.ThreadPoolExecutor = concurrent.futures.ThreadPoolExecutor(
        max_workers=2)
    blocking_socket_future = main_loop.run_in_executor(
        executer,
        blocking_socket,
        app_config.InterfaceName,
        services_manager.add_queue,
        services_manager.add_service
    )

    # block until signal shutdown
    while not EXIT_PROGRAM:
        # await services_manager.status()
        print("main loop - output")
        await asyncio.sleep(5)
    #
    await services_manager.stop_all_services()

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
