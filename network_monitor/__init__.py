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
    service_manager = None
    if args.interface is not None:
        # check validate choice and start process
        service_manager = Service_Manager(args.interface)
        service_manager.start()

    else:
        if args.list_gateways:
            print("gateways: ")
            for k, v in netifaces.gateways().items():
                print(f"\taddress family: {k}, interface: {v}")

        if args.list_interfaces:
            print(f"interfaces: {netifaces.interfaces()}")

        sys.exit(0)

    # exit cleanly
    def signal_handler(sig, frame):
        service_manager.stop()
        sys.exit(0)

    signal.signal(signal.SIGTSTP, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # blocking loop
    while True:
        time.sleep(0.05)
