from __future__ import annotations

import re
from html import unescape
from typing import Any, List, Optional

from bs4 import BeautifulSoup

from utils.transformer import ToAsync

try:
    __import__("lxml")
    HTML_PARSER = "lxml"

except ImportError:
    HTML_PARSER = "html.parser"


class Soup:
    """Class to handle bs4 requests"""

    def __init__(self, string: str) -> None:
        self.data = string
        self.soup = BeautifulSoup(self.data, HTML_PARSER)

    def __parse_text(self, st: str) -> str:
        return (
            re.sub(r" +", " ", unescape(st).replace("\n", " ").replace("\t", " "))
            if st
            else ""
        )

    @ToAsync()
    def find_one(self, soup: BeautifulSoup, name: str, **kwargs) -> str:
        if finder := soup.find(name, **kwargs):
            return self.__parse_text(finder.text)

        return ""

    # @ToAsync()
    def find_all(
        self, soup: BeautifulSoup, name: str, **kwargs: Any
    ) -> Optional[List[str]]:
        if finder := soup.find_all(name, kwargs):
            return [self.__parse_text(i.text) for i in finder]

        return []
