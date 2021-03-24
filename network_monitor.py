import netifaces
import argparse


def main():

    basic_parser = argparse.ArgumentParser(description="monitor ethernet network packets.",add_help=True)

    # add arguments
    basic_parser.add_argument('-i','--interface',action='store',choices=netifaces.interfaces(),type=str,help= 'specify which interface to monitor')
    basic_parser.add_argument('-li','--list-interfaces',action='store_true',help='list all available interfaces')
    basic_parser.add_argument('-lg','--list-gateways',action='store_true',help='list all available gateways')
    
    # parse arguments
    args = basic_parser.parse_args()

    if args.interface is not None:
        # check validate choice and start process
        pass
    else:

        if args.list_gateways:
            print("gateways: ")
            for k,v in netifaces.gateways().items():
                print(f"\taddress family: {k}, interface: {v}")
        
        if args.list_interfaces:
            print(f"interfaces: {netifaces.interfaces()}")
   

if __name__ == "__main__":
    exit(main())