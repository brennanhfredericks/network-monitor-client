from .protocol_utils import Unknown


class Parser(object):
    protocol_parsers = {}

    def __init__(self, name: str):
        self.name = name

    # def register(self, identifier, parser):
    #     # need to implement check for
    #     self.protocol_parsers[identifier] = parser

    def process(self, protocol, raw_bytes):
        try:
            self._encap = self.protocol_parsers[protocol](raw_bytes)
            print(self._encap)
        except KeyError:
            # would any other exception occur?
            # add loggin functionality here
            self._encap = Unknown(f"Parser for {self.name} {protocol} not implemented")
            print(f"Parser for {self.name} {protocol} not implemented")


IP_Protocols = Parser("IP Protocols")
Ethernet_Types = Parser("Ethernet Types")
