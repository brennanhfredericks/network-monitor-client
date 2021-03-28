def get_protocol(out_packet, cls):
    """ return a the provide protocol form the packet, if protocol not found return None """

    if out_packet is None:
        return None
    elif isinstance(out_packet, cls):
        return out_packet
    else:
        out = get_protocol(out_packet.upper_layer(), cls)

    return out