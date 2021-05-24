# network monitor client

---

## description

  An asynchronous python 3 application to parse network frames received by a wired network interface controller operating in promiscuous mode.

  The application consist of the following services:
  - interface listener
    - opens a low level socket on a network interface controller and captures all ethernet packets processed by the controller. This operation requires super user privileges. 
  - packet parser
    - processes all captured packets into protocol objects contatining the metadata
      - only support protocols listed below
      - and protocols where the implementation are available
    - packet filter
      - filters captured packets based on user defined filters
        - filters are protocol name and protocol atrributes key value pairs
  - packet submitter
    - sends captured packets metadata to network monitor server
    - if network monitor server not available, stores processed data locally 

---

## basic usage:

- only test on unix system

### command line:
  - list availiable network interfaces
  `python3 network_monitor.py -li` 
  - list gateways
  `python3 network_monitor.py -lg`
  - listen on network interface, requires superuser privileges
  `sudo python3 network_monitor.py -i <interface name> `
  - generate configuration template file ini format
  `python3 network_monitor.py -gcf <configuration filename>`
  - load configuration file
  `python3 network_monitor.py -lcf <configuration filename>`

### filters:
  - a filter is a JSON structure containing protocols which themself are JSON structures containing the protocol attributes
  - all protocol attributes in the filter needs to match a captured packet attributes, for the filter to be triggered.
  - examples:
    - filter based on `IPv4` and `TCP` protocol attributes 
      ```json 
      {
        "IPv4":{
          "source_address":"127.0.0.1",
          "destination_address":"127.0.0.1"
        },
        "TCP":{
          "destination_port":5000,
        }
      }
      ```
    - filter all packets captured on the `lo` interface that contain the `IPv4` protocol
      ```json 
      {
        "AF_Packet":{"ifname":"lo"},
        "IPv4":{}
      }
      ```
  
---

### todo:


#### high priority
  - Application terminated by Kernel, out of memory due to queue not being cleared.
    - []  rewrite startup code to use two threads. interface_listener_service blocking. (how to create asycio low level socket connection?)
    - [] move from init to network.py 
  - Implement flag to filter all traffic generate by application from being send to network monitor server

#### medium priority
  - Implement flag to verbose output of application, remove print functions and replace with stdout and stderr pipes
  
#### low priority
  - 802.2 Packet
    - Other Individual LSAP address parsers (`IEEE 802.1 Bridge Spanning Tree Protocol`, `ARPANET Address Resolution Protocol (ARP)` etc)
  - IPv6 extension headers
    - Implement parsers to extract information from extension headers (`Routing`,`Fragment`,`Authentication Header` etc) 
  - Checksum verifier - requires 1's complement in verification algorithm
    - `IPV4`
    - `IPv6`
    - `ICMP`
    - `ICMPv6`
    - `IGMP`
    - `TCP`
    - `UDP`

---

### implemented
  
  - Ethertypes
    - 2048: Internet Protocol version 4 (IPv4)
    - 2054: Address Resolution Protocol (ARP)
  	- 34525: Internet Protocol Version 6 (IPv6)
  	- 8192: Cisco Discovery Protocol (CDP)
  	- 35020: Link Layer Discovery Protocol (LLDP)
  - IP protocols
    - 1: Internet Control Message Protocol (ICMP)
  	- 2: Internet Group Message Protocol (IGMP)
  	- 6: Transmission Control Protocol (TCP)
  	- 17: User Datagram Protocol (UDP)
  	- 58: Internet Control Message Protocol for IPv6 (ICMPv6)
  - 802.2 LLC PDU
  	- 170: SNAP Extension Used


# Development Setup 
- Networking stack and docker issues, ip address are also chaning with start up

### changes

#### 2021/05/17
- changed application from threaded to asynchronous
- added asynchronous logger, only logs to stderr and stdout