from pathlib import Path

from .task import BurnsubTask
from .tasks import Tasks
from .path import get_file_format
from ..env import config

SUPPORT_NORMAL_SUFFIXES = [
    "mp4",
    "wmv",
    "avi",
    "webm",
    "mkv",
    "rmvb",
    "mpeg",
    "flv",
    "mpg",
    "m4v",
    "3gp",
    "mov",
    "qt",
    "mp2",
    "mpe",
    "mpv",
    "ogg",
]
# VIDEO_SUFFIXES = ["yuv", "wmv", "webm", "vob", "svi", "roq", "rmvb", "rm", "ogv", "ogg", "nsv", "mxf", "ts", "mpg", "mpeg", "m2v", "mp2", "mpe", "mpv", "mp4", "m4p", "m4v", "mov", "qt", "mng", "mkv", "flv", "f4v", "f4p", "f4a", "f4b", "drc", "avi", "asf", "amv", "3gp", "3g2", "mxf", "m2p", "ps", "m2ts", "mts", "iso", "avchd", "swf"]


def filter_file(file_path: Path, tasks: Tasks):
    file_format = get_file_format(file_path)
    if file_format in SUPPORT_NORMAL_SUFFIXES:
        srt_file_path = Path(file_path.with_suffix(".srt"))
        if srt_file_path.exists():
            Tasks.add_task(BurnsubTask(file_path, srt_file_path, "srt"))
            return

        ass_file_path = Path(file_path.with_suffix(".ass"))
        if ass_file_path.exists():
            Tasks.add_task(BurnsubTask(file_path, ass_file_path, "ass"))
            return


def traverse(dir_path: Path, tasks):
    for child in dir_path.iterdir():
        if child.is_file():
            filter_file(child, tasks)
        elif child.is_dir():
            traverse(child, tasks)


# filter video file
def filter(path: Path = Path(config["input"]), tasks: Tasks = Tasks()):
    if path.is_file():
        filter_file(path, tasks)
    elif path.is_dir():
        traverse(path, tasks)


# def check_dvd_folder(dir_path):
#     for child in dir_path.iterdir():
#         if child.is_file() and len(child.suffixes) > 0 and child.suffixes[-1][1:].lower() in SUPPORT_DVD_FOLDER_SUFFIXES:
#             return child.parent
#         elif child.is_dir():
#             res = check_dvd_folder(child)
#             if res:
#                 return res
#     return None
