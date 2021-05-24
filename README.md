# network monitor client

---

## description

  An asynchronous python 3 application to parse network frames received by a wired network interface controller operating in promiscuous mode.

  The application consist of the following services:
  - interface listener
    - opens a low level socket on a network interface controller and captures all ethernet packets processed by the controller. This operation requires super user privileges. 
  - packet parser
    - processes all captured packets into protocol objects contatining the metadata
      - supported protocols listed below
    - packet filter
      - filters captured packets based on user defined filters
        - filters are defined using nested key value pairs. The protocol names, protocol atrributes and attributes values are the key value pairs
  - packet submitter
    - sends captured packets metadata to network monitor server
    - if network monitor server not available, stores processed data locally 
---

## basic usage:

- Unix system

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
          "Source_Address":"127.0.0.1",
          "Destination_Address":"127.0.0.1"
        },
        "TCP":{
          "Destination_Port":5000,
        }
      }
      ```
    - filter all packets captured on the `lo` interface that contain the `IPv4` protocol
      ```json 
      {
        "AF_Packet":{"Interface_Name":"lo"},
        "IPv4":{}
      }
      ```
  
---

### todo:

- [] Filter Selection Behaviour
  - [] by default filter any data generete between the application and the monitor server. 

- [x] Only parser traffic on the interface specified by the user. if a computer a has multiple virtual interfaces that use the (physical) interface specified by the user. The captured data also contains data from the virtual interfaces (docker, tunnels etc).  

- [] When monitor server is available clear any locally stored data. create a asynchronous task that loads and pushes local data into data_channel. update timestamp?
  clear data from disk if it has been added to the queue. 
- [] If server is unavailable spawn an asynchronous task (prediocally based on retryinterval) to check if server is available. when available change storage submmission from `local` to `remote` and clear locally stored data
- [] 802.2 Packet
  - Other Individual LSAP address parsers (`IEEE 802.1 Bridge Spanning Tree Protocol`, `ARPANET Address Resolution Protocol (ARP)` etc)
- [] IPv6 extension headers
    - Implement parsers to extract information from extension headers (`Routing`,`Fragment`,`Authentication Header` etc) 
- [] Checksum verifier - requires 1's complement in verification algorithm
    - `IPV4`
    - `IPv6`
    - `ICMP`
    - `ICMPv6`
    - `IGMP`
    - `TCP`
    - `UDP`

- [] Remove multiple threads and multiple asynchronous loops not need. Found root cause of exponetial growth queue issue. Make application fully asynchronous with the listener service running in a executer (raw non blocking sockets?). Current implementation
  - Main asynchronous loop application which spawn three threads
    - 1: Interface Listener Service (Synchronous loop):
      - blocking raw socket that push the binary data into queue for processing by another service
    - 2: Packet Parser Service (Asynchronous loop)
      - parsers and filters packets
    - 3: Packet Submitter Service (Asynchronous loop)
      - write processed data to local storage or remote storage
  - Application terminates using SIGINT, SIGTSTP and wait for all queue to process before gracefully shutting down spawned threads and main asynchronous loop
- [] Only await for asynchronous storage task at the end of thread or when storage mode changes . use introspection to retrieve asynchronous loop tasks). await causes a bottleneck when remote storage mode is activated. Could also be the coupling between database and api
- [] Implement TCP,UDP stream tracker (partial implementation in notebook)
- [] Rewrite and expand test cases  
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

  - Asynchronous stream and file logging
  - Asynchronous status update
  - Asynchronous shutdown 
# Development Setup Issues 
  - If the client application and network monitor server traffic passes through the same intefaces () the client will reprocess the traffic generated by the application as new network which will result in a Out of memory issue an application being killed by OS.

  - solution filter traffic at port and ip address level



