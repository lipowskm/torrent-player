from pathlib import Path
import shutil
import tempfile

from torrent_player import utils
from torrent_player.torrent import File


def test_count_video_files():
    """Should recognize most popular video formats."""
    extensions = ("mp4", "avi", "mkv", "wmv", "flv")
    files = [File(name=f"video.{extension}", size=1) for extension in extensions]
    assert utils.count_video_files(files) == 5
    files.append(File(name=f"not_video.srt", size=1))
    assert utils.count_video_files(files) == 5


def test_is_video_file():
    """Should recognize most popular video formats."""
    assert utils.is_video_file("movie.mkv")
    assert utils.is_video_file("movie.mp4")
    assert utils.is_video_file("movie.avi")
    assert not utils.is_video_file("file.txt")


def test_convert_size():
    """Should return approximate string representation of size."""
    assert utils.convert_size(0) == "0 B"
    assert utils.convert_size(5) == "5.0 B"
    assert utils.convert_size(1024) == "1.0 KiB"
    assert utils.convert_size(1048576) == "1.0 MiB"
    assert utils.convert_size(2000000) == "1.91 MiB"
    assert utils.convert_size(1073741824) == "1.0 GiB"


def test_find_file_containing():
    """Should return absolute path to file containing input text in its name."""
    file_name = "file.txt"
    test_dir = tempfile.mkdtemp()
    path = Path(test_dir) / file_name
    with open(path, "wb") as file:
        file.close()
    try:
        assert not utils.find_file_containing("test", test_dir)
        assert Path(utils.find_file_containing("file", test_dir)) == path
        assert Path(utils.find_file_containing("le.txt", test_dir)) == path
    finally:
        shutil.rmtree(test_dir)
