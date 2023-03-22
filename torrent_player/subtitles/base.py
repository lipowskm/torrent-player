from abc import ABC, abstractmethod

from torrent_player.torrent import Torrent


class SubtitlesHandler(ABC):
    @abstractmethod
    def download_subtitles_from_path(self, video_file_path: str, output_path: str):
        pass

    @abstractmethod
    def download_subtitles_from_torrent(
        self,
        torrent: Torrent,
        file_index: int,
        output_path: str,
    ) -> str:
        pass
