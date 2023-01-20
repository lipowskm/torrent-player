import re
import subprocess
import tempfile
from pathlib import Path
from typing import Literal, get_args


class WebtorrentError(Exception):
    pass


class Webtorrent:
    _STREAM_OUTPUTS = Literal["vlc", "mpv"]

    def __init__(self, entrypoint: str = "webtorrent") -> None:
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
        self, command: str, magnet: str, output_dir: str, timeout: int
    ) -> subprocess.CompletedProcess:
        if not output_dir:
            output_dir = tempfile.mkdtemp()
        else:
            path = Path(output_dir)
            path.mkdir(exist_ok=True)
            output_dir = str(path.absolute())
        try:
            result = subprocess.run(
                " ".join([self.entrypoint, "-o", output_dir, command, f'"{magnet}"']),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise WebtorrentError("Timeout expired while trying to download torrent.")
        if result.returncode:
            raise WebtorrentError(
                "Error during downloading.\n\n"
                f"More details:\n{result.stdout.decode('utf-8')}"
            )
        return result

    def download_meta(
        self, magnet: str, output_dir: str = None, timeout: int = 60
    ) -> str:
        result = self._run_download("downloadmeta", magnet, output_dir, timeout)
        stdout = result.stdout.decode("utf-8")
        match = re.search("[a-zA-Z]:[\\\\/](?:.+[\\\\/])*(.+\\.torrent)", stdout)
        if not match:
            raise WebtorrentError(
                "Unable to find downloaded .torrent file\n\n" f"More details:\n{stdout}"
            )
        return str(Path(match.group()).absolute())

    def download(self, magnet: str, output_dir: str = None, timeout: int = 3600) -> None:
        self._run_download("download", magnet, output_dir, timeout)

    def stream(
        self, magnet: str, output: _STREAM_OUTPUTS, file_index: int = None
    ) -> None:
        if output not in get_args(self._STREAM_OUTPUTS):
            raise ValueError(
                f"Parameter 'output' accepts only: {get_args(self._STREAM_OUTPUTS)}"
            )
        args = [self.entrypoint, f"--{output}"]
        if file_index:
            args.extend([f"--select", str(file_index)])
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
