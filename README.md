
# TODO

  - Add logging
  - need to implement test cases for advance logger, logger updated to log AF_Packet as well
  - remove hack in 802.3 __parse_upper_layer_protocol to test 802.2 packets
  - Add functionality to follow TCP stream
  - Packet_Submitter
    - make post functionality asynchronous, to avoid blocking
  - 802.2 Packet
    - only implemented SNAP Extension for Individual LSAP addresses
    - 
  - IPv4 outstanding functionality:
    - implement header checksum comparison
  
  - IPv6 outstanding functionality:
    - implement parsers for decoding extension headers, only extracting header first two bytes to get to upper layer protocol
      extension headers is part of IP protocol numbers. need specific list of extension headers to stop while loop extraction
  - ICMP outstanding functionality
    - implement checksum verifier
  - ICMPv6 outstanding functionality
    -  implement checksum verifier
  - IGMP outstanding functionality
    - implement checksum verifier
  - TCP outstanding functionality
    - implement checksum verifier
  - UDP outstanding functionality 
    - implement checksum verifier

# Outstanding
  - Packet Submitter
    - use to send data monitor server api
    - if monitor server not available buffer data into queue (to reduce write operation) and write file or insert into sqlite database
      - periodically check if server is available, if available send store data and clear sqlite database


# Implemented

    - Network Listerner
      - functionality listen on a single ethernet interface
    
    - Packet Parser
      - ethernet interface origin
      - 802.3 packet
        - ethertypes
          - 2048: Internet Protocol version 4 (IPv4)
          - 2054: Address Resolution Protocol (ARP)
          - 34525: Internet Protocol Version 6 (IPv6)
          - 8192: Cisco Discovery Protocol
          - 35020: Link Layer Discovery Protocol
        
        - ip protocols
          - 1: Internet Control Message Protocol (ICMP)
          - 2: Internet Group Message Protocol (IGMP)
          - 6: Transmission Control Protocol (TCP)
          - 17: User Datagram Protocol (UDP)
          - 58: Internet Control Message Protocol for IPv6 (ICMPv6)
          - 

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