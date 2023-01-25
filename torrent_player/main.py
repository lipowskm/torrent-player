import argparse
from dataclasses import dataclass
import logging
import sys

from rich.console import Console
from rich.logging import RichHandler

from torrent_player.cli import cli
from torrent_player.tpb import TPB
from torrent_player.utils import count_video_files
from torrent_player.webtorrent import Webtorrent

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(show_path=False)]
)

log = logging.getLogger("rich")


@dataclass
class Args:
    query: str


def parse_args() -> Args:
    parser = argparse.ArgumentParser(
        prog="torrentplayer",
        description="Stream any torrent from ThePirateBay to your favourite player",
    )

    parser.add_argument("query")

    return Args(**vars(parser.parse_args()))


def main() -> None:
    try:
        args = parse_args()
        console = Console()
        tpb = TPB()
        webtorrent = Webtorrent()

        torrents = tpb.search(args.query)
        if not torrents:
            log.error("No torrents matching query found")
            sys.exit(1)
        console.print("\n")

        torrent = cli.choose_torrent(console, torrents)
        file_index = None
        log.info("Scanning metadata...")
        video_files_count = count_video_files(torrent.files)
        if video_files_count == 0:
            log.error("No video files found inside torrent")
            sys.exit(1)
        if video_files_count > 1:
            log.info("Multiple video files found inside torrent")
            file_index = cli.choose_file_from_torrent(console, torrent)
        log.info("Launching VLC...")
        webtorrent.stream(torrent.magnet, "vlc", file_index=file_index)
    except KeyboardInterrupt:
        log.error("Exiting...")
        sys.exit(1)
    except Exception as e:
        log.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
