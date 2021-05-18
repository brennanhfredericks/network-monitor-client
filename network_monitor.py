import netifaces
import argparse
import asyncio
import os
import signal
import functools
from asyncio import Task
from network_monitor import generate_configuration_template, load_config_from_file
from network_monitor.configurations import DevConfig
from typing import Optional, Dict

# execute in its own thread


async def async_aware_ops():
    ...
# configure start up manager

# execute in its own_thread


async def async_ops():
    ...


async def start_app(interface_name: Optional[str] = None, configuration_file: Optional[str] = None) -> None:

    # get main asyncio loop
    main_loop = asyncio.get_running_loop()

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
    # services_manager: Service_Manager = Service_Manager()

    # main loop blocking part
    EXIT_PROGRAM: bool = False

    def signal_handler(*args):
        # use parent scope variable
        nonlocal EXIT_PROGRAM
        print("application starting exist process")
        EXIT_PROGRAM = True

    main_loop.add_signal_handler(
        signal.SIGTSTP, functools.partial(signal_handler))
    main_loop.add_signal_handler(
        signal.SIGINT, functools.partial(signal_handler))

    # block until signal shutdown
    while not EXIT_PROGRAM:
        # await services_manager.status()
        print("main loop - output")
        await asyncio.sleep(1)
    #
    # await main_loop.create_task(asyncio.sleep(5))

    main_loop.stop()


def main(args: argparse.Namespace) -> int:

    # first do info args with with starting application
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
