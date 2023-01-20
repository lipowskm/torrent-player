import math
from typing import Iterable

from torrent_player.constants import VIDEO_EXTENSIONS
from torrent_player.torrent import File


def count_video_files(files: Iterable[File]) -> int:
    counter = 0
    for file in files:
        if file.name.endswith(VIDEO_EXTENSIONS):
            counter += 1
    return counter


def is_video_file(name: str) -> bool:
    return name.lower().endswith(VIDEO_EXTENSIONS)


def convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"
