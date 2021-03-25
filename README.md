
# TODO
    - add logging
    - 802.2 Packet
      - need to investigate IEEE 802.2 packet upper layer data and parser it out if possible. confirm parsing
    - IPv4 outstanding functionality:
      - implement header checksum comparison
      - implement options field extraction when IHL is bigger than 5
    - ARP outstanding functionality
      - sender protocol address should be decode based on requested protocol. should not assume it will always be IPv4
        The permitted PTYPE values share a numbering space with those for EtherType. 
    
# Implemented

  - Network Listerner
    - functionality listen on a single ethernet interface
  
  - Packet Parser
    - ethernet interface origin
    - 802.3 packet
      - (ethertype between 0 and 1500) encapsulation of 802.2 Packet. could be wrong need to confirm
      - (ethertype 2048) Internet Protocol version 4 (IPv4)

## Command Line
    - basic command line interface to start the network-monitor with the following argument options
      - list all interfaces (-li, --list-interfaces)
      - list all gateways (-lg, --list-gateways)
      - specify interface to monitor (-i, --interfaces) with interface name
      - 
## Service Manager
    - service_manager to start and stop threads and provide listening interface info
      - added methods to retrieve the interface addresses,
      - added error handling for starting service
      
## Network Listener Serivce
    - Ethernet port listener
      - create low level interface directly to network devices
        - linux
        - windows (to be tested)
      - added queue to transfer data (bytes, address)  between threads

# Possible Additional Features
    - additional commads:
      - set server address
      - generate empty config file
      - start using config file
      - add functionality to listen on multiple interfaces

# For consideration 
    - use interface addresses as identifier when posting data to server
    - could use sub classing for service trait
    - need to investigate unpacking 802.2 packet, might be wrong, check commet at code

    - could implement protocols and register them (in a dictionary for lookup), would then avoid the need manually specify protocol look up tables and easily expandable


