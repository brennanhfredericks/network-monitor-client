import binascii
import base64
import json
import os
from collections.abc import Iterable
import pytest


def load_filev2(filename, log_dir="./data"):
    """load file and return raw pack bytes"""

    path = None
    if isinstance(filename, str):
        path = os.path.join(log_dir, filename)
        if not os.path.exists(path):
            raise ValueError(f"{path} doesn't exists")
        path = [path]
    elif isinstance(filename, Iterable):
        path = []
        for f in filename:
            path_ = os.path.join(log_dir, f)
            if not os.path.exists(path_):
                raise ValueError(f"{path_} doesn't exists")
            path.append(path_)
    else:
        raise ValueError("only support str and Interable(str)")

    for p in path:
        with open(p, "r") as fin:
            while True:
                af_packet = fin.readline()
                if len(af_packet) == 0:
                    break
                af_packet = base64.b64decode(af_packet)
                packet = base64.b64decode(fin.readline())

                yield json.loads(af_packet), packet


# should support path, str
def load_file(filename, log_dir="./data"):
    """load file and return raw pack bytes"""

    path = None
    if isinstance(filename, str):
        path = os.path.join(log_dir, filename)
        if not os.path.exists(path):
            raise ValueError(f"{path} doesn't exists")
        path = [path]
    elif isinstance(filename, Iterable):
        path = []
        for f in filename:
            path_ = os.path.join(log_dir, f)
            if not os.path.exists(path_):
                raise ValueError(f"{path_} doesn't exists")
            path.append(path_)
    else:
        raise ValueError("only support str and Interable(str)")

    for p in path:
        with open(p, "rb") as fin:
            while line := fin.readline():
                yield binascii.a2b_base64(line)


def test_load_single_file():

    load_file("raw_ipv4_output.lp")


def test_load_file_list():

    load_file(["raw_ipv4_output.lp", "raw_ipv6_output.lp", "raw_arp_output.lp"])


def test_load_file_tuple():

    load_file(("raw_ipv4_output.lp", "raw_ipv6_output.lp", "raw_arp_output.lp"))


@pytest.mark.xfail(raises=ValueError)
def test_load_single_file_fail():
    load_file(0)


@pytest.mark.xfail(raises=ValueError)
def test_load_file_list_fail():

    load_file(["raw_ipv4_output.lp", 0, "raw_arp_output.lp"])


@pytest.mark.xfail(raises=ValueError)
def test_load_file_tuple_fail():

    load_file(("raw_ipv4_output.lp", "raw_ipv6_output.lp", 1))


def load_unknown_file(filename, log_dir="./data"):
    """load raw unknown packets"""
    path = None
    if isinstance(filename, str):
        path = os.path.join(log_dir, filename)
        if not os.path.exists(path):
            raise ValueError(f"{path} doesn't exists")
        path = [path]
    elif isinstance(filename, Iterable):
        path = []
        for f in filename:
            path_ = os.path.join(log_dir, f)
            if not os.path.exists(path_):
                raise ValueError(f"{path_} doesn't exists")
            path.append(path_)
    else:
        raise ValueError("only support str and Interable(str)")

    for p in path:
        with open(p, "rb") as fin:
            while True:
                info = fin.readline()
                if len(info) == 0:
                    break
                info = binascii.a2b_base64(info)

                info = info.decode("utf-8").split("_")
                packet = binascii.a2b_base64(fin.readline())
                layer_protocol, identifier = "_".join(info[:2]), info[-1]

                yield layer_protocol, identifier, packet
