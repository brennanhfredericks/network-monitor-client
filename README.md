
# TODO
    - add logging
    - 
    
# Implemented

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


