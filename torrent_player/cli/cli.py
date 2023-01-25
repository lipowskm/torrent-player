from rich.console import Console
from rich.table import Table

from torrent_player.cli.colors import error
from torrent_player.torrent import Torrent
from torrent_player.utils import convert_size, is_video_file


def choose_torrent(console: Console, torrents: list[Torrent]) -> Torrent:
    table = get_torrents_table(torrents)
    console.print(table)
    option = None
    while not option:
        option = console.input("Enter torrent number to play: ")
        if option.isnumeric() and int(option) > 0:
            try:
                torrent = torrents[int(option) - 1]
                return torrent
            except IndexError:
                console.print(error("Invalid value, try again"))
                option = None
                continue
        if option.lower() in ["n", "p"]:
            raise NotImplementedError
        console.print(error("Invalid value, try again"))
        option = None


def choose_file_from_torrent(console: Console, torrent: Torrent) -> int:
    table = get_torrent_files_table(torrent)
    console.print(table)
    option = None
    while not option:
        option = console.input("Enter video file number to play: ")
        if option.isnumeric() and int(option) > 0:
            try:
                index = int(option) - 1
                file_name = torrent.files[index].name
                if is_video_file(file_name):
                    return index
                console.print(error("This is not a video file"))
                option = None
                continue
            except IndexError:
                console.print(error("Invalid value, try again"))
                option = None
                continue
        if option.lower() in ["n", "p"]:
            raise NotImplementedError
        console.print(error("Invalid value, try again"))
        option = None


def get_torrents_table(torrents: list[Torrent]) -> Table:
    table = Table(title="Torrents found:", title_style="bold")
    table.add_column("Number", justify="right")
    table.add_column("Title", justify="left")
    table.add_column("Upload date", justify="center")
    table.add_column("Size", justify="right")
    table.add_column("Seeders", justify="right")
    table.add_column("Leechers", justify="right")

    for i, torrent in enumerate(torrents, 1):
        table.add_row(
            str(i),
            torrent.title,
            torrent.upload_date,
            torrent.size,
            str(torrent.seeders),
            str(torrent.leechers),
        )

    return table


def get_torrent_files_table(torrent: Torrent) -> Table:
    table = Table(title=torrent.title, title_style="bold")
    table.add_column("Number", justify="right")
    table.add_column("File name", justify="left")
    table.add_column("Size", justify="right")

    for i, file in enumerate(torrent.files, 1):
        table.add_row(
            str(i),
            file.name,
            convert_size(file.size),
        )

    return table
