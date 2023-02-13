from __future__ import annotations

import datetime
from typing import List, Optional, Tuple, Union

from bs4 import BeautifulSoup

try:
    __import__("lxml")
    HTML_PARSER = "lxml"
except ImportError:
    HTML_PARSER = "html.parser"


class Extractor:
    def __init__(self, file_name: str) -> None:
        with open(rf"profiles/{file_name}", "r") as f:
            self.soup: BeautifulSoup = BeautifulSoup(f, HTML_PARSER)

        self._headers: List[str] = []
        self._values: List[str] = []

        self._get_all_headers()
        self._get_all_values()

    def _get_all_values(self):
        val = self.soup.find_all("div", class_="profile-info-value")
        self._values = [i.text.replace("\n", "").replace("\t", "").strip() for i in val]

    def _get_all_headers(self):
        head = self.soup.find_all("div", class_="profile-info-name")
        self._headers = [i.text.strip() for i in head]

    def get_data(self) -> List[Tuple[str, str]]:
        return list(zip(self._headers, self._values))
