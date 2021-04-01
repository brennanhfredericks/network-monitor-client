
# TODO

  - Add type hints and annotations and start using mypy
  - Add functionality to group TCP packets into stream
  - Packet_Submitter
    - functionality to asynchronously post data to server, and test when server available
    - functionality to remove log files when data has is succesfully posted to server
  - 802.2 Packet
    - Individual LSAP addresses parsers. Only implmented SNAP extension parser
  - IPv4 outstanding functionality:
    - implement checksum verifier
  - IPv6 outstanding functionality:
    - implement parsers for decoding extension headers, only extracting header first two bytes to get to upper layer protocol
    - extension headers is part of IP protocol numbers. need specific list of extension headers to stop while loop extraction.
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
    - 
        - periodically check if server is available, if available send store data and clear disk data
  - Packet Filter
    - use filter packets based on protocols and flags

# Implemented

    - Network Listerner
      - functionality listen on a single ethernet interface
    
    - Packet Submitter
      - if monitor server not available buffer data into memory file (to reduce write operation) and write to disk at n intervals 

    - Packet Parser
      - AF packet
      - 802.3 packet
        - ethertypes
          - 2048: Internet Protocol version 4 (IPv4)
          - 2054: Address Resolution Protocol (ARP)
          - 34525: Internet Protocol Version 6 (IPv6)
          - 8192: Cisco Discovery Protocol (CDP)
          - 35020: Link Layer Discovery Protocol (LLDP)
        
        - ip protocols
          - 1: Internet Control Message Protocol (ICMP)
          - 2: Internet Group Message Protocol (IGMP)
          - 6: Transmission Control Protocol (TCP)
          - 17: User Datagram Protocol (UDP)
          - 58: Internet Control Message Protocol for IPv6 (ICMPv6)
          
      - 802.2 Packet 
        - 802.2 LLC PDU Header
          - 170: SNAP Extension Used
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
    - could use inheritance for services and protocols
    - could wrap protocol registering with decorater, cleaner.
    - investigate checksum calculation alogorithm and implement to verify checksum values
    