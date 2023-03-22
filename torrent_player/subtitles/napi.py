import hashlib
from io import BytesIO
import logging
import os
from pathlib import Path
import shutil
import tempfile
from time import sleep
from typing import Optional

from charset_normalizer import from_bytes
from py7zlib import Archive7z, ArchiveError
import requests
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from torrent_player.process import Process
from torrent_player.subtitles.base import SubtitlesHandler
from torrent_player.torrent import Torrent
from torrent_player.utils import find_file_containing
from torrent_player.webtorrent import Webtorrent


console = Console(theme=Theme({"logging.level.success": "green"}))
log = logging.getLogger("napi")
log.propagate = False
log.handlers.clear()
handler = RichHandler(show_path=False, console=console)
formatter = logging.Formatter("[NapiProjekt] %(message)s", datefmt="[%X]")
handler.setFormatter(formatter)
log.addHandler(handler)


class SubtitlesError(Exception):
    """Base exception class, not meant to be raised directly."""


class SubtitlesNotFoundError(SubtitlesError):
    """Raised when subtitles are not found for specified video file."""


class SubtitlesEncodingError(SubtitlesError):
    """Raised when there is a problem with subtitles (de/en)coding."""


class NapiprojektHandler(SubtitlesHandler):
    _ARCHIVE_PASSWORD = "iBlm8NTigvru0Jr0"

    def download_subtitles_from_path(
        self, video_file_path: str, output_path: Optional[str] = None
    ) -> str:
        """
        Download subtitles using local path to video file.

        :param video_file_path: path to video file
        :param output_path: path to directory or full path containing file
            name and extension
        """
        file_hash = self._get_file_hash(video_file_path)
        if not file_hash:
            raise SubtitlesNotFoundError("Unable to determine file hash")
        url = self._get_url(file_hash)
        archive = requests.get(url).content
        unzipped = self._unzip(archive)
        if not unzipped:
            raise SubtitlesNotFoundError("No subtitles found for specified file")
        subs = self._encode(self._unzip(archive))
        if not output_path:
            output_path = tempfile.mkdtemp()
        output_path = Path(output_path)
        if output_path.is_dir():
            subs_name = Path(video_file_path).with_suffix(".srt").name
            output_path = output_path / subs_name
        with open(output_path.absolute(), "wb") as file:
            file.write(subs)
        return str(output_path)

    def download_subtitles_from_torrent(
        self,
        torrent: Torrent,
        file_index: int,
        output_path: Optional[str] = None,
        retries: int = 30,
    ) -> str:
        """
        Download subtitles using Torrent object.

        :param torrent: Torrent object
        :param file_index: optional file index matching file inside torrent
        :param output_path: path to directory or full path containing file
            name and extension
        :param retries: more retries means higher chance to get subtitles,
            but longer execution time
        """
        webtorrent = Webtorrent()
        torrent_path = tempfile.mkdtemp()
        process = Process(
            target=webtorrent.download, args=(torrent.magnet, torrent_path, file_index)
        )
        try:
            process.start()
            i = 0
            file_name = Path(torrent.files[file_index].name).name
            log.info(f"Downloading subtitles for {file_name!r}...")
            last_exception = None
            while i < retries:
                if process.exception:
                    exception, traceback = process.exception
                    raise exception
                file_path = find_file_containing(file_name, torrent_path)
                if not file_path:
                    sleep(1)
                    i += 1
                    continue
                try:
                    subs_path = self.download_subtitles_from_path(
                        file_path, output_path
                    )
                except SubtitlesError as e:
                    last_exception = e
                    sleep(1)
                    i += 1
                    continue
                log.log(70, f"Subtitles found for file {file_name!r}")
                return subs_path
            else:
                if last_exception:
                    log.error(str(last_exception))
                    raise last_exception
                else:
                    msg = "Unable to download torrent file for subtitles lookup"
                    log.error(msg)
                    raise SubtitlesNotFoundError(msg)
        finally:
            process.kill()
            shutil.rmtree(torrent_path, ignore_errors=True)

    def _get_url(self, file_hash: str):
        """Constructs URL to get subtitles from."""
        return (
            "http://napiprojekt.pl"
            "/unit_napisy"
            "/dl.php?l=PL"
            f"&f={file_hash}"
            f"&t={self._cipher(file_hash)}"
            "&v=other"
            "&kolejka=false"
            "&nick="
            "&pass="
            f"&napios={os.name}"
        )

    @staticmethod
    def _get_file_hash(video_file_path: str) -> Optional[str]:
        """
        Get MD5 hash created using content of first 10 MiBs of a video file.
        Used in request query to NapiProjekt API.
        """
        _10_MBS = 10485760
        if Path(video_file_path).stat().st_size < _10_MBS:
            return None
        md5_hash_gen = hashlib.md5()
        with open(video_file_path, mode="rb") as movie_file:
            content_of_first_10mbs = movie_file.read(_10_MBS)
        md5_hash_gen.update(content_of_first_10mbs)
        return md5_hash_gen.hexdigest()

    @staticmethod
    def _cipher(file_hash: str):
        """What the fuck?"""
        idx = [0xE, 0x3, 0x6, 0x8, 0x2]
        mul = [2, 2, 5, 4, 3]
        add = [0, 0xD, 0x10, 0xB, 0x5]

        b = []
        for i in range(len(idx)):
            a = add[i]
            m = mul[i]
            i = idx[i]

            t = a + int(file_hash[i], 16)
            v = int(file_hash[t : t + 2], 16)
            b.append(("%x" % (v * m))[-1])

        return "".join(b)

    def _unzip(self, archive: bytes) -> Optional[bytes]:
        """Unzip archive returned by NapiProjekt API."""
        try:
            buffer = BytesIO(archive)
            archive = Archive7z(buffer, password=self._ARCHIVE_PASSWORD)
            return archive.getmember(0).read()
        except ArchiveError:
            return None

    @staticmethod
    def _encode(subs: bytes) -> bytes:
        """Decode and then encode subs just in case."""
        match = from_bytes(subs).best()
        if not match:
            raise SubtitlesEncodingError("Unable to guess subtitles encoding")
        base_encoding = match.encoding
        encodings = ("cp1250", "cp1251", "cp1252", "cp1253", "cp1254", "utf-8")
        try:
            decoded_subs = subs.decode(base_encoding)
        except UnicodeDecodeError:
            raise SubtitlesEncodingError(
                f"Unable to decode subs using {base_encoding!r} encoding"
            )
        for encoding in encodings:
            try:
                return decoded_subs.encode(encoding)
            except UnicodeEncodeError:
                continue
        else:
            raise SubtitlesEncodingError(
                f"Unable to encode subs using any of following encodings: {encodings!r}"
            )
