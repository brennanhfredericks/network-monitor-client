import configparser


def generate_template_configuration(config_name: str):

    """ used to generate template configuration for easy setup """

    # create config file
    config = configparser.ConfigParser()

    # defualt configuration variables use for development
    config["DEFAULT"] = {
        "PacketParserServiceLog": "./logs/parser_service/",
        "ApplicationLog": "./logs/app",
        "PacketSubmitterServiceLog": "./logs/submitter_service/",
        "PacketSubmitterServiceUrl": "http://127.0.0.1:5000/packets",
    }
