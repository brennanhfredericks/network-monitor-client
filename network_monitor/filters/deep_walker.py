def get_protocol(out_packet, cls):
    """ return the  provided protocol from the packet else None, when protocol not in packet"""

    if out_packet is None:
        return None
    elif isinstance(out_packet, cls):
        return out_packet
    else:
        out = get_protocol(out_packet.upper_layer(), cls)

    return out


def present_protocols(out_packet):
    """ return identifier of all protocols present in the packet as """

    # top packet has no identifier, only upper layers
    protocols = []
    out = out_packet
    loop = True
    while loop:
        out = out.upper_layer()
        if out is not None:
            if hasattr(out, "identifier"):
                protocols.append(out.identifier)
            else:
                loop = False
                raise ValueError(f"{out} has not identifier attribute")
        else:
            loop = False
    return protocols


def which_protocols_in_packet(out_packet, proto_list):
    """return a dictionary where they key is the protocol identifier and the value is
    a boolean,true if provided protocol(s) in the packet else None, when protocol(s) not in packet"""

    ret = {k.identifier: False for k in proto_list}

    # update dictionary

    for identi in present_protocols(out_packet):
        ret[identi] = True

    return ret
