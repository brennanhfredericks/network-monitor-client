import netifaces
import collections
import queue
import time
import sys


class Service_Manager(object):
    def __init__(self, interface_name):
        self._ifname = interface_name
        self._ifaddress = netifaces.ifaddresses(interface_name)
        self._services = collections.OrderedDict()

    @property
    def interface_addresses(self):
        return self._ifaddress

    @property
    def address_family(self):
        return list(self._ifaddress.keys())

    @property
    def ipv4_address(self):

        if netifaces.AF_INET in self._ifaddress.keys():
            return self._ifaddress[netifaces.AF_INET]

        return None

    @property
    def ipv6_address(self):

        if netifaces.AF_INET6 in self._ifaddress.keys():
            return self._ifaddress[netifaces.AF_INET6]

        return None

    @property
    def link_layer_address(self):

        if netifaces.AF_LINK in self._ifaddress.keys():
            return self._ifaddress[netifaces.AF_LINK]

        return None

    def start_service(self, service_name: str, service_obj):
        # start service
        service_obj.start()

        # hack that wait to check if any errors are pushed on to data queue
        time.sleep(0.1)

        if service_obj._data_queue.qsize() == 2:
            item = service_obj._data_queue.get()
            if isinstance(item, Exception):
                (type_, value, traceback) = service_obj._data_queue.get()
                print(f"Error starting {service_name} service: {item}")

                self.stop_all_services()
                sys.exit(0)

        # add service to Order dict
        self._services[service_name] = service_obj

    def stop_all_services(self):

        for k, v in self._services.items():
            # stop service and join thread
            v.stop()
            print(f"{k} service stopped")

        self._services.clear()
