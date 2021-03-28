def get_protocol(out_packet, cls):
    """ return the  provided protocol from the packet else None, when protocol not in packet"""

    if out_packet is None:
        return None
    elif isinstance(out_packet, cls):
        return out_packet
    else:
        out = get_protocol(out_packet.upper_layer(), cls)

    return out


def collect_protocols(out_packet):
    """ return identifier of all protocols present in the packet as """

    # top packet has no identifier, only upper layers
    protocols = []
    while out := out_packet.upper_layer() is not None:
        if hasattr(out, "identifier"):
            protocols.append(out.identifier)
        else:
            raise ValueError(f"{out} has not identifier attribute")

    return protocols


def is_protocols_in_packet(out_packet, cls):
    """ return true if provided protocol(s) in the packet else None, when protocol(s) not in packet """

    ...