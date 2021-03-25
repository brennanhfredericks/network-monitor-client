
# TODO

    - add logging
    - 802.2 Packet
      - need to investigate IEEE 802.2 packet upper layer data and parser it out if possible. confirm parsing
    - IPv4 outstanding functionality:
      - implement header checksum comparison
      - implement options field extraction when IHL is bigger than 5
    - IPv6 outstanding functionality:
      - implement DS field and ECN field extraction from Traffic_Class
      - implement parsers for decoding extension headers, only extracting header first two bytes to get to upper layer protocol
    - ICMP outstanding functionality
      - implement checksum to compare values
      - implement parser to decode different control message,
    - ICMPv6 outstanding functionality
      -  implement checksum to compare values
      -  implement parser to decode different control message
    - IGMP outstanding functionality
      - implement checksum to compare values
      - implement parser for message types
    - TCP outstanding functionality
      - implement checksum to compare values
      - implement parser for options part
    - UDP outstanding functionality 
      - implement checksum to compare values
      - payload should be determined based length field value
      
# Implemented

  - Network Listerner
    - functionality listen on a single ethernet interface
  
  - Packet Parser
    - ethernet interface origin
    - 802.3 packet
      - ethertypes
        - between 0 and 1500: encapsulation of 802.2 Packet. could be wrong need to confirm
        - 2048: Internet Protocol version 4 (IPv4)
        - 2054: Address Resolution Protocol (ARP)
      
      - ipv4 protocols
        - 1: Internet Control Message Protocol (ICMP)
        - 2: Internet Group Message Protocol (IGMP)
        - 6: Transmission Control Protocol (TCP)
        - 58: Internet Control Message Protocol for IPv6 (ICMPv6)

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

    - could implement protocols and register them (in a dictionary for lookup), would then avoid the need manually specify protocol look up tables and easily  expandable
    - restructure code in to module form, in order to implement test and seperate from source code. have a look at `internet protocol suite` when modularising source code.


