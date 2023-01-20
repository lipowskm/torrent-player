import random
from urllib.parse import urlparse, urlunparse

import requests
from lxml import html

from torrent_player.constants import USER_AGENTS
from torrent_player.torrent import Torrent


def get_headers() -> dict[str, str]:
    """
    The Pirate Bay blocks requests (403 Forbidden)
    basing on User-Agent header, so it's probably better to rotate them.
    User-Agents taken from:
    https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
    """
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "origin_req_host": "thepiratebay.se",
    }


class TPBParser:
    def __init__(self, html_str: str) -> None:
        self._search_results_rows = html.fromstring(html_str).xpath(
            '//tr[td[@class="vertTh"]]'
        )

    @property
    def torrents(self) -> list[Torrent]:
        return [self._get_torrent(row) for row in self._search_results_rows]

    @staticmethod
    def _get_torrent(row: html.HtmlElement) -> Torrent:
        title_element = row.find('.//a[@class="detLink"]')
        title = title_element.text
        url = title_element.get("href")
        magnet = row.xpath('.//a[starts-with(@href, "magnet")]/@href')[0]
        description = row.findtext('.//font[@class="detDesc"]')
        description_items = description.replace("\xa0", " ").split(", ")
        upload_date = description_items[0].replace("Uploaded ", "")
        size = description_items[1].replace("Size ", "")
        seeders, leechers = map(int, row.xpath('.//td[@align="right"]/text()'))
        return Torrent(
            title=title,
            url=url,
            magnet=magnet,
            upload_date=upload_date,
            size=size,
            seeders=seeders,
            leechers=leechers,
        )


class TPB:
    def __init__(self, base_url: str = "https://tpb.party") -> None:
        self.base_url = base_url

    def search(self, query: str) -> list[Torrent]:
        parsed_url = urlparse(self.base_url)
        url = urlunparse(parsed_url._replace(path=f"search/{query}/1/99/200"))
        response = requests.get(url, headers=get_headers())
        return TPBParser(response.text).torrents
