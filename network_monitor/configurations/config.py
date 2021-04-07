import configparser
import os


def generate_template_configuration(config_name: str):

    """ used to generate template configuration for easy setup """

    # create config file
    config = configparser.ConfigParser()

    # defualt configuration variables use for development
    config["DEFAULT"] = {
        "InterfaceName": "enp0s3",
        "UnknownProtocols": "./logs/application/unknown_protocols",
        "Log": "./logs/application/general",
        "Local": "./logs/submitter_service",
        "Url": "http://127.0.0.1:5000/packets",
        "Filter": {
            "AF_Packet": {"ifname": "lo"},
            "IPv4": {"destination_address": "127.0.0.01"},
            "TCP": {"destination_port": 5000},
        },
    }

    with open(os.path.join("./", f"{config_name}.cfg"), "w") as fout:
        config.write(fout)

    # Specify interface on which the ethernet listener service should be started.
    # Requires super user priviliages to change the interface to operate in promiscous
    # [ListenerService]
    # InterfaceName = "enp0s3"

    # Specify application settings. global settings some of which affect other services.
    # [Application]
    # Log = "./logs/application/general/"
    # UnknownProtocols = "./logs/application/unknown_protocols"
    # FilterAllApplicationTraffic = True

    # Specify submitter service setting.
    # [SubmitterService]
    # Local = "./logs/submitter_service/"
    # Url = "http://127.0.0.1:5000/packets"
    # RetryInterval = 300

    # configure filter settings
    # [Filter]
    # Definition = {"AF_Packet":{"ifname":"lo"},"TCP":{}}

    # [Filter]
    # Definition = {"ICMP":{}}