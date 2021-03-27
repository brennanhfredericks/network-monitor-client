import binascii
import os

DIR = "./data"


def load_file(filename):

    path = os.path.join(DIR, filename)

    if not os.path.exists(path):
        raise ValueError(f"{path} doesn't exists")

    with open(path, "rb") as fin:
        while line := fin.readline():
            yield binascii.a2b_base64(line)
