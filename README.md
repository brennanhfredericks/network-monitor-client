# network monitor
---
a python 3 library to parse network frames received by a wired network interface controller operating in promiscuous mode

Each protocol is defined in the appropriate layer and register, unknown protocols are logged to file for analysis and to add to definition

# basic usage:

## command line:
  - list availiable network interfaces
  `python3 network_monitor.py -li` 
  - list gateways
  `python3 network_monitor.py -lg`
  - listen on network interface, requires superuser privileges
  `sudo python3 network_monitor.py -i <interface name> `
## Installation

### TODO
    - [] create str mapping for all protocols, to be used for comparison or index 
    - [] Packet_Filter
      - [] Add functionality to check if user defined filter is valid. if not valid raise ValueError
    - [] Add type hints and annotations and start using mypy
    - [] Add functionality to group TCP packets into stream
    - [] Packet_Submitter
      - [] functionality to asynchronously post data to server, and test when server available
      - [] functionality to remove log files when data has is succesfully posted to server
    - [] 802.2 Packet
      - [] Individual LSAP addresses parsers. Only implmented SNAP extension parser
    - [] IPv4 outstanding functionality:
      - [] implement checksum verifier
    - [] IPv6 outstanding functionality:
      - [] implement parsers for decoding extension headers, only extracting header first two bytes to get to upper layer protocol
      - [] extension headers is part of IP protocol numbers. need specific list of extension headers to stop while loop extraction.
    - [] ICMP outstanding functionality
      - [] implement checksum verifier
    - [] ICMPv6 outstanding functionality
      - [] implement checksum verifier
    - [] IGMP outstanding functionality
      - [] implement checksum verifier
    - [] TCP outstanding functionality
      - [] implement checksum verifier
    - [] UDP outstanding functionality 
      - [] implement checksum verifier
    - [] manually added link layer protocols to class name lookup table (hack), implement with register functionality?

### Outstanding
    - Packet Filter


### Implemented

    - [x] Network Listerner
      - [x] functionality listen on a single ethernet interface
    
    - [x] Packet Submitter
      - [x] periodically check if server is available, if available send store data and clear disk data

    - [x] Packet Parser
      - [x] AF packet
      - [] 802.3 packet
        - [] ethertypes
          - [x] 2048: Internet Protocol version 4 (IPv4)
          - [x] 2054: Address Resolution Protocol (ARP)
          - [x] 34525: Internet Protocol Version 6 (IPv6)
          - [x] 8192: Cisco Discovery Protocol (CDP)
          - [x] 35020: Link Layer Discovery Protocol (LLDP)
        
        - [x] ip protocols
          - [x] 1: Internet Control Message Protocol (ICMP)
          - [x] 2: Internet Group Message Protocol (IGMP)
          - [x] 6: Transmission Control Protocol (TCP)
          - [x] 17: User Datagram Protocol (UDP)
          - [x] 58: Internet Control Message Protocol for IPv6 (ICMPv6)
          
      - [x] 802.2 Packet 
        - [x] 802.2 LLC PDU Header
          - [x] 170: SNAP Extension Used
          - 


### Command Line
    - basic command line interface to start the network-monitor with the following argument options
      - list all interfaces (-li, --list-interfaces)
      - list all gateways (-lg, --list-gateways)
      - specify interface to monitor (-i, --interfaces) with interface name
  
      

### Possible Additional Features
    - additional commads:
      - set server address
      - generate empty config file
      - start using config file
      - add functionality to listen on multiple interfaces

### For consideration 
    - use interface addresses as identifier when posting data to server
    - could use inheritance for services and protocols
    - could wrap protocol registering with decorater, cleaner.
    - investigate checksum calculation alogorithm and implement to verify checksum values
    - The sniffer can prevent this by configuring a firewall to block ICMP traffic responses
    - currently using empty protocol objects as key index, which is larger than int, i.e. bytes usage