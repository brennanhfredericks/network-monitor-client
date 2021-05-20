import os
import time
import base64
import asyncio
import aiofiles
import sys

from aiologger.handlers.streams import AsyncStreamHandler
from asyncio import Task
from typing import Dict, Union, Any, Optional, List
from functools import lru_cache


from .protocol_utils import Unknown
from logging import Formatter
from aiologger import Logger

from .layer import Layer_Protocols


class __Parser:
    """ class to register all packet parsers for various levels"""

    __protocol_parsers: Dict[int, Dict[int, Any]] = {}
    __protocol_str_lookup: Dict[str, Any] = {}

    def __init__(self) -> None:

        # init layer protocols
        for layer_protocol in Layer_Protocols:
            self.__protocol_parsers[layer_protocol] = {}

        self.__logger: Optional[Logger] = None
        self.__loop: Optional[asyncio.AbstractEventLoop] = None
        self.__log: Optional[str] = None
        self.__fname: str = f"raw_unknown_protocols_{int(time.time())}.lp"

    @property
    def parsers(self) -> Dict[int, Dict[int, Any]]:

        return self.__protocol_parsers

    def set_output_directory(self, output_directory: str) -> None:

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        stream_format = Formatter(
            "%(asctime)s -:- %(name)s -:- %(levelname)s"
        )

        logger = Logger(name=__name__)

        # create handles
        stream_handler = AsyncStreamHandler(
            stream=sys.stderr, formatter=stream_format)
        logger.add_handler(stream_handler)

    def set_async_loop(self, loop: asyncio.AbstractEventLoop):
        self.__loop = loop

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
        except KeyError as e:
            # add logging functionality
            if self.__loop is not None:

                self.__loop.create_task(
                    self.std_logger(
                        f"{class_name} not a vaild protocol class name"
                    )
                )

        else:
            return res

    @lru_cache
    def _reverse_protocols_str_lookup(self) -> Dict[Any, int]:

        return {v: k for k, v in self.__protocol_str_lookup.items()}

    def get_protocol_name_by_class(self, cls: Any) -> str:
        """ return name of class"""

        rev_protocol_str = self._reverse_protocols_str_lookup()
        try:
            res = rev_protocol_str[cls]
        except KeyError as e:
            # add logging functionality
            if self.__loop is not None:

                self.__loop.create_task(
                    self.std_logger(
                        f"{cls} not register in lookup table"
                    )
                )

        else:
            return res

    async def file_logger(self, info: str, raw_bytes: bytes) -> None:
        async with aiofiles.open(os.path.join(self.__log, self.__fname), "ab") as fout:
            await fout.write(base64.b64encode(info.encode()))
            await fout.write(base64.b64encode(raw_bytes))

    async def std_logger(self, message: str) -> None:
        await self.__logger.exception(message)

    def parse(self, layer: Layer_Protocols, identifier: int, raw_bytes: bytes) -> Any:
        """ 
            used to lookup registered protocol parsers and instantiate the protocol parser with the raw bytes 
        """
        # all asynchronous task are retrieved via introspection and awaited before exist
        try:
            res = self.__protocol_parsers[layer][identifier](raw_bytes)

        except KeyError as e:
            if self.__loop is not None:
                self.__loop.create_task(
                    self.std_logger(
                        f"Protocol Not Implemented Exception - Layer: {layer}, identifier: {identifier}"
                    )
                )
                self.__loop.create_task(
                    self.file_logger(
                        f"{layer}_{identifier}",
                        raw_bytes
                    )
                )

        except Exception as e:
            if self.__loop is not None:
                self.__loop.create_task(
                    self.std_logger(
                        f"Protocol Exception: {e}"
                    )
                )

            return Unknown("no protocol parser available", identifier, raw_bytes)
        else:
            return res


Protocol_Parser: __Parser = __Parser()
