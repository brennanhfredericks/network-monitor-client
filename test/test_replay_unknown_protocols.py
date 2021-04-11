from test_load_data import load_unknown_file
import os


def replay_unknown():
    base_dir = "./logs/application/unknown_protocols/"

    for f in os.listdir(base_dir):
        for l_proto, identi, packet in load_unknown_file(f, log_dir=base_dir):

            print(l_proto, identi, packet)
            # break
        # break
    assert False


def test_replay_unknown():
    replay_unknown()