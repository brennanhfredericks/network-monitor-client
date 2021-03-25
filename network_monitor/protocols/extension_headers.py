class IPv6_Ext_Headers(object):
    """ wrapper for the different ipv6 extension headers """

    # hack need specify callable objects
    EXT_HEADER_LOOKUP = {
        0: "Hop by Hop_Options",
        43: "Routing",
        44: "Fragment",
        50: "Encapsulating Security Payload (ESP)",
        51: "Authentication Header (AH)",
        59: "No Next Header - inspect payload",
        60: "Destination Options",
        135: "Mobility",
        139: "Host Identity Protocol",
        140: "Shim6 Protocol",
        253: "Reserved",
        254: "Reserved",
    }

    def __init__(self):
        self._headers = []

    def parse_extension_headers(self, next_header, raw_bytes):
        # When extension headers are present in the packet this field indicates which extension header follows.
        # The values are shared with those used for the IPv4 protocol field, as both fields have the same function
        # If a node does not recognize a specific extension header, it should discard the packet and send a Parameter Problem message (ICMPv6 type 4, code 1).
        # Value 59 (No Next Header) in the Next Header field indicates that there is no next header whatsoever following this one, not even a header of an upper-layer protocol. It means that, from the header's point of view, the IPv6 packet ends right after it: the payload should be empty.[1] There could, however, still be data in the payload if the payload length in the first header of the packet is greater than the length of all extension headers in the packet. This data should be ignored by hosts, but passed unaltered by routers.

        def parse_header(remaining_raw_bytes):
            __next_header, __ext_header_len = struct.unpack(
                "! B B", remaining_raw_bytes[:2]
            )

            return (
                __next_header,
                remaining_raw_bytes[:__ext_header_len],
                remaining_raw_bytes[__ext_header_len:],
            )

        if next_header not in self.EXT_HEADER_LOOKUP.keys():
            # upper-layer protocol
            return self._headers, next_header, raw_bytes
        else:
            # for clarity
            r_raw_bytes = raw_bytes
            ext_header = next_header

            # extract extion until upper layer protocol is reached
            while ext_header in self.EXT_HEADER_LOOKUP.keys():
                # should parse header to append id and data
                new_ext_header, ext_header_data, r_raw_bytes = parse_header(r_raw_bytes)

                # need to implement Extion headers parsers to decode headers
                self._headers.append((ext_header, ext_header_data))
                ext_header = new_ext_header

            return self._headers, ext_header, r_raw_bytes
