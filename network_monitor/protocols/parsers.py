import os
import time
import base64
import asyncio
import aiofiles

from asyncio import Task
from typing import Dict, Union, Any, Optional, List
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

    async def init_asynchronous_operation(self, undefined_output_directory: str, logger: Logger(), task_list: List[Task]) -> None:

        if not os.path.exists(undefined_output_directory):
            os.makedirs(undefined_output_directory)

        self.__log = undefined_output_directory
        self.logger: Logger = logger
        self.task_list: List[Task] = []

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

        rev_protocol_str = self._reverse_protocols_str_lookup()
        try:
            res = rev_protocol_str[cls]
        except IndexError as e:
            # add logging functionality
            raise ValueError(f"{cls} not register in lookup table")
        else:
            return res

    async def unknown_storage(self, info: str, raw_bytes: bytes) -> None:
        async with aiofiles.open(os.path.join(self.__log, self.__fname), "ab") as fout:
            await fout.write(base64.b64encode(info.encode()))
            await fout.write(base64.b64encode(raw_bytes))

    async def log(self, message: str) -> None:
        await self.logger.exception(message)

    # task to asynchronous execution loop
    def execute_async(self, coro, *args) -> None:

        self.task_list.append(
            asyncio.create_task(
                coro(*args)
            )
        )

    def parse(self, layer: Layer_Protocols, identifier: int, raw_bytes: bytes) -> Any:
        """ use to register parser"""
        try:
            res = self.__protocol_parsers[layer][identifier](raw_bytes)

        # asnyc
        except KeyError as e:
            self.execute_async(
                self.log,
                f"Protocol Not Implemented Exception - Layer: {layer}, identifier: {identifier}"

            )
            self.execute_async(
                self.unknown_storage,
                f"{layer}_{identifier}",
                raw_bytes,

            )

        except Exception as e:
            self.execute_async(
                self.log,
                f"Protocol Exception: {e}"

            )

            return Unknown("no protocol parser available", identifier, raw_bytes)
        else:
            return res


Protocol_Parser: Parser = Parser()
