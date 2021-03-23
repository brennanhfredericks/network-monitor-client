# Starting Commandline Options
    - add commad line arguments to list all interfaces, gateways using netifaces
    - e.g. commands:
        - network_monitor -interface 'enp0s3'
        - network_monitor -list-interfaces , -list-gateways



- use interface addresses as identifier when posting data to server


# Network Listener
    - look up os and create low level socket. requires sudo permission
    - keep listing until stopped

# Packet Processer
    - parse raw packet into format and drop data

# Reporter
    - send data to server, if not available log to sqlite database
    - when server is available transfer sqlite database to monitor server 
