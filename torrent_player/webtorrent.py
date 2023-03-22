from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Optional, get_args

from torrent_player import constants


class WebtorrentError(Exception):
    pass


class Webtorrent:
    _TEMP_PATH = Path(tempfile.gettempdir()) / "webtorrent"

    def __init__(self, entrypoint: str = "webtorrent") -> None:
        """Wrapper for webtorrent-cli tool."""
        result = subprocess.run(
            ["where", entrypoint],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            shell=False,
        )
        if result.returncode:
            raise WebtorrentError(
                f"{entrypoint!r} command is unavailable in system shell.\n"
                "To install webtorrent-cli, first install Node.js "
                "and then run 'npm install webtorrent-cli -g'"
            )
        self.entrypoint = entrypoint

    def _run_download(
        self,
        command: str,
        magnet: str,
        output_dir: Optional[str],
        file_index: Optional[int],
        timeout: int,
    ) -> str:
        """Base downloading logic."""
        if not output_dir:
            output_dir = tempfile.mkdtemp()
        else:
            path = Path(output_dir)
            path.mkdir(exist_ok=True)
            output_dir = str(path.absolute())
        args = [self.entrypoint, "--out", output_dir]
        if file_index:
            args.extend(["--select", str(file_index)])
        args.extend([command, f'"{magnet}"'])
        process = subprocess.Popen(
            " ".join(args),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            if process.returncode:
                raise WebtorrentError(
                    "Error during Webtorrent downloading.\n\n"
                    f"More details:\n{str(stdout)}"
                )
            return str(stdout)
        except subprocess.TimeoutExpired:
            raise WebtorrentError(
                "Timeout expired while trying to download with Webtorrent."
            )
        # except KeyboardInterrupt:
        #     process.kill()
        #     process.communicate()

    def download_meta(
        self, magnet: str, output_dir: Optional[str] = None, timeout: int = 30
    ) -> str:
        """
        Download .torrent file with metadata.

        :param magnet: torrent magnet link
        :param output_dir: output directory.
                           If none is given, file will be saved in temporary directory.
        :param timeout: timeout in seconds
        :returns: path to downloaded .torrent file
        """
        stdout = self._run_download("downloadmeta", magnet, output_dir, None, timeout)
        match = re.search("[a-zA-Z]:[\\\\/](?:.+[\\\\/])*(.+\\.torrent)", stdout)
        if not match:
            raise WebtorrentError(
                "Unable to find downloaded .torrent file\n\n" f"More details:\n{stdout}"
            )
        return str(Path(match.group()).absolute())

    def download(
        self,
        magnet: str,
        output_dir: Optional[str] = None,
        file_index: Optional[int] = None,
        timeout: int = 3600,
    ) -> None:
        """
        Download torrent.

        :param magnet: torrent magnet link
        :param output_dir: output directory
        :param file_index: if given, downloads only single file specified by the index
        :param timeout: timeout in seconds
        """
        self._run_download("download", magnet, output_dir, file_index, timeout)

    def stream(
        self,
        magnet: str,
        output: constants.PLAYERS,
        file_index: Optional[int] = None,
        subtitles: Optional[str] = None,
    ) -> None:
        """
        Stream torrent to video player.

        :param magnet: torrent magnet link
        :param output: output directory
        :param file_index: if given, streams file specified by the index,
                           otherwise streams first file available
        :param subtitles: path to subtitles
        """
        if output.lower() not in get_args(constants.PLAYERS):
            raise ValueError(
                f"Parameter 'output' accepts only: {get_args(constants.PLAYERS)}"
            )
        args = [self.entrypoint, f"--{output}", "--not-on-top"]
        if subtitles:
            args.extend(["--subtitles", f'"{subtitles}"'])
        if file_index is not None:
            args.extend(["--select", str(file_index)])
        args.append(f'"{magnet}"')
        result = subprocess.run(
            " ".join(args),
            shell=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        if result.returncode:
            raise WebtorrentError(
                "Unable to stream specified magnet link.\n\n"
                f"More details:\n{result.stdout.decode('utf-8')}"
            )

    def cleanup(self) -> None:
        """Remove all temporary files used by webtorrent-cli."""
        shutil.rmtree(self._TEMP_PATH, ignore_errors=True)
