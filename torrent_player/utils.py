import math
from pathlib import Path
from typing import Iterable, Optional

from torrent_player.constants import VIDEO_EXTENSIONS
from torrent_player.torrent import File


def count_video_files(files: Iterable[File]) -> int:
    return len([file for file in files if is_video_file(file.name)])


def is_video_file(name: str) -> bool:
    return name.lower().endswith(VIDEO_EXTENSIONS)


def convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    size_names = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def find_file_containing(text: str, dir_path: str) -> Optional[str]:
    for path in Path(dir_path).glob("**/*"):
        if text in str(path):
            return str(path)
    return None
