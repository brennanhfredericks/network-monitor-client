import os
import time
import base64
import asyncio

from typing import Dict, Union, Any, Optional
from functools import lru_cache


from .protocol_utils import Unknown
from aiologger import Logger

from .layer import Layer_Protocols


class Parser:
    """ class to register all packet parsers for various levels"""

    __protocol_parsers: Dict[int, Dict[int, Any]] = {}
    __protocol_str_lookup: Dict[str, Any] = {}

    def __init__(self) -> None:

        # init layer protocols
        for layer_protocol in Layer_Protocols:
            self.__protocol_parsers[layer_protocol] = {}

        self.logger: Optional[Logger] = None
        self.__log: Optional[str] = None
        self.__fname: str = f"raw_unknown_protocols_{int(time.time())}.lp"

    @property
    def parsers(self) -> Dict[int, Dict[int, Any]]:

        return self.__protocol_parsers

    def set_log_directory(self, log_dir: str) -> None:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.__log = log_dir

    async def set_logger(self, logger: Logger()) -> None:
        self.logger = Logger

    def register(self, layer: Layer_Protocols, identifier: int, protocol_parser: Any):
        # check if dataclass and callable
        self.__protocol_parsers[layer][identifier] = protocol_parser
        self.__protocol_str_lookup[protocol_parser.__name__] = protocol_parser

    def _register_protocol_class_name(self, class_name, protocol_parser):
        self.__protocol_str_lookup[class_name] = protocol_parser

    def get_protocol_class_by_name(self, class_name: str) -> Any:
        """ return an empty protocol class used in comparison """
        try:
            res = self.__protocol_str_lookup[class_name]
        except IndexError as e:
            # add logging functionality
            raise ValueError(f"{class_name} not a vaild protocol class name")
        else:
            return res

    @lru_cache
    def _reverse_protocols_str_lookup(self) -> Dict[Any, int]:

        return {v: k for k, v in self.__protocol_str_lookup.items()}

    def get_protocol_name_by_class(self, cls: Any) -> str:
        """ return name of class"""
        # inefficient,only use to ensure the latest version is use cach
        rev_protocol_str = self._reverse_protocols_str_lookup()
        try:
            res = rev_protocol_str[cls]
        except IndexError as e:
            # add logging functionality
            raise ValueError(f"{cls} not register in lookup table")
        else:
            return res

    async def log(self, message: str) -> None:
        # add items here to event loop?
        # await self.logger.exception("Sd")
        ...

    def parse(self, layer: Layer_Protocols, identifier: int, raw_bytes: bytes) -> Any:
        """ use to register parser"""
        try:
            res = self.__protocol_parsers[layer][identifier](raw_bytes)

        except KeyError as e:
            path: str = os.path.join(self.__log, self.__fname)
            with open(path, "ab") as fout:
                info = f"{layer}_{identifier}"
                fout.write(base64.b64encode(info.encode()))
                fout.write(base64.b64encode(raw_bytes))
            # task = asyncio.create_task(self.log(
            #    f"Protocol Not Implemented Exception - Layer: {layer}, identifier: {identifier}"
            # ))

        except Exception as e:

           # asyncio.create_task(self.log(f"Protocol Exception: {e}"))
            return Unknown("no protocol parser available", identifier, raw_bytes)
        else:
            return res


Protocol_Parser: Parser = Parser()
