from dataclasses import dataclass, field
from pathlib import Path
import shutil

from torrentool.api import Torrent as _Torrent

from torrent_player.webtorrent import Webtorrent


@dataclass(frozen=True)
class File:
    name: str
    size: int


@dataclass(frozen=True)
class Torrent:
    title: str
    url: str
    magnet: str
    upload_date: str
    size: str
    seeders: int
    leechers: int
    _files: list[File] = field(init=False, repr=False)

    @property
    def files(self) -> list[File]:
        """List of files inside torrent."""
        try:
            self._files
        except AttributeError:
            webtorrent = Webtorrent()
            torrent_path = webtorrent.download_meta(self.magnet)
            try:
                torrent = _Torrent.from_file(torrent_path)
                files = [
                    File(Path(file.name).name, file.length) for file in torrent.files
                ]
                object.__setattr__(self, "_files", files)
            finally:
                parent_dir = Path(torrent_path).parent
                shutil.rmtree(parent_dir)
        return self._files
