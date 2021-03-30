
# TODO

    - add logging
    - need to implement test cases for advance logger
    - remove hack in 802.3 __parse_upper_layer_protocol to test 802.2 packets
    - 
    - 802.2 Packet
      - only implemented SNAP Extension for Individual LSAP addresses
    - IPv4 outstanding functionality:
      - implement header checksum comparison
    
    - IPv6 outstanding functionality:
      - implement DS field and ECN field extraction from Traffic_Class
      - implement parsers for decoding extension headers, only extracting header first two bytes to get to upper layer protocol
        extension headers is part of IP protocol numbers. need specific list of extension headers to stop while loop extraction
    - ICMP outstanding functionality
      - implement checksum to compare values
      - need to test
      - implement parser to decode different control message,
    - ICMPv6 outstanding functionality
      -  implement checksum to compare values
      -  implement parser to decode different control message
    - IGMP outstanding functionality
      - implement checksum to compare values
      - implement parser for message types
    - TCP outstanding functionality
      - implement checksum to compare values
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
          - 17: User Datagram Protocol (UDP)
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
    - could use inheritance for service trait
    - need to investigate unpacking 802.2 packet, might be wrong, check commet at code

    - solved circular reference imports with delayed import. only import when function is called
    - could wrap protocol registering with decorater, cleaner. the identifier could be a field in the class it self

    - could add raw_logger to commandline args or create a separete groups for them.