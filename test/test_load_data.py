import binascii
import os
from collections.abc import Iterable
import pytest

DIR = "./data"

# should support path, str
def load_file(filename):
    """load file and return raw pack bytes"""
    print(type(filename))
    path = None
    if isinstance(filename, str):
        path = os.path.join(DIR, filename)
        if not os.path.exists(path):
            raise ValueError(f"{path} doesn't exists")
        path = [path]
    elif isinstance(filename, Iterable):
        path = []
        for f in filename:
            path_ = os.path.join(DIR, f)
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