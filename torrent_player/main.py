import argparse
from dataclasses import dataclass
import logging
from pathlib import Path
import shutil
import subprocess
import sys

import requests
from rich.console import Console
from rich.logging import RichHandler

from torrent_player.cli import cli
from torrent_player.subtitles.napi import NapiprojektHandler, SubtitlesError
from torrent_player.tpb import TPB
from torrent_player.utils import count_video_files, is_video_file
from torrent_player.webtorrent import Webtorrent

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(show_path=False)]
)
logging.addLevelName(70, "SUCCESS")

log = logging.getLogger("main")


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
    console = Console()
    tpb = TPB()
    webtorrent = Webtorrent()
    handler = NapiprojektHandler()

    def cleanup(*_) -> None:
        if sys.platform == "win32":
            try:
                subprocess.run(
                    ["taskkill", "/f", "/im", "vlc.exe"],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                )
            except KeyboardInterrupt:
                pass
            webtorrent.cleanup()
            try:
                if subs_path:
                    shutil.rmtree(Path(subs_path).parent, ignore_errors=True)
            except NameError:
                pass

    if sys.platform == "win32":
        import win32api
        win32api.SetConsoleCtrlHandler(cleanup)

    args = parse_args()
    try:
        torrents = tpb.search(args.query)
        if not torrents:
            log.error("No torrents matching query found")
            sys.exit(1)
        console.print("\n")

        torrent = cli.choose_torrent(console, torrents)
        log.info("Scanning metadata...")
        video_files_count = count_video_files(torrent.files)
        if video_files_count == 0:
            log.error("No video files found inside torrent")
            sys.exit(1)
        elif video_files_count == 1:
            file_index = next(
                torrent.files.index(file)
                for file in torrent.files
                if is_video_file(file.name)
            )
        else:
            log.info("Multiple video files found inside torrent")
            file_index = cli.choose_file_from_torrent(console, torrent)
        try:
            subs_path = handler.download_subtitles_from_torrent(torrent, file_index)
        except SubtitlesError:
            subs_path = None
            log.warning("File will be played without subtitles")
        log.info("Launching VLC...")
        webtorrent.stream(
            torrent.magnet, "vlc", file_index=file_index, subtitles=subs_path
        )
        cleanup()
        sys.exit(0)
    except (EOFError, KeyboardInterrupt):
        log.info("Exiting...")
        cleanup()
        sys.exit(0)
    except requests.exceptions.ConnectionError:
        log.error(
            "Connection error. Please check if your internet connection is working."
        )
        cleanup()
        sys.exit(1)
    except Exception as e:
        log.error(str(e))
        cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
