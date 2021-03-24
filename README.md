
# TODO
    - Add services class to start and stop threads used to retrieve and process information
    - use queues to pass information between threads

# Implemented
    - basic command line interface implemented with the following argument options
      - list all interfaces (-li, --list-interfaces)
      - list all gateways (-lg, --list-gateways)
      - specify interface to monitor (-i, --interfaces) with interface name

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
