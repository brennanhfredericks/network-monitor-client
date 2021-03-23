import netifaces

print(netifaces.gateways())
#print(netifaces.ifaddresses())
print(netifaces.interfaces())
"""
Starting options
    - add commad line arguments to list all interfaces, gateways using netifaces
    - commad line args:
        - network_monitor -interface 'enp0s3'
        - network_monitor -list-interfaces , -list-gateways

    - use interface addresses as identifier when posting data



Network Listener
    - look up os and create low level socket. requires sudo permission
    - keep on listing until stopped

Packet Processer
    - parse raw packet into format and drop data

Reporter
    - send data to server, if not available log to sqlite database
    - when server is available transfer sqlite database to monitor server 

"""