
# TODO

    - use queues to pass information between threads

# Implemented
## Command Line
    - basic command line interface to start the network-monitor with the following argument options
      - list all interfaces (-li, --list-interfaces)
      - list all gateways (-lg, --list-gateways)
      - specify interface to monitor (-i, --interfaces) with interface name
## Service Manager
    - service_manager to start and stop threads and provide listening interface info
      - add methods to retrieve the interface addresses info, to be used as a unique identifier 

## Network Listener Serivce
    - Ethernet port listener
      - create low level interface directly to network devices
        - linux
        - windows


# Possible Additional Features
## Starting Commandline Options
    - additional commads:
        - set server address
        - generate empty config file
        - start using config file
        - add functionality to listen on multiple interfaces
- use interface addresses as identifier when posting data to server


## Network Listener
    - look up os and create low level socket. requires sudo permission
    - keep listing until stopped

## Packet Processer
    - parse raw packet into format and drop data

## Reporter
    - send data to server, if not available log to sqlite database
    - when server is available transfer sqlite database to monitor server 
