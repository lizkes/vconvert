from pathlib import Path

from .task import Task, Tasks
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
SUPPORT_DVD_SUFFIXES = ["m2ts", "mts", "ts", "avchd"]
SUPPORT_ISO_SUFFIXES = ["iso"]
# VIDEO_SUFFIXES = ["yuv", "wmv", "webm", "vob", "svi", "roq", "rmvb", "rm", "ogv", "ogg", "nsv", "mxf", "ts", "mpg", "mpeg", "m2v", "mp2", "mpe", "mpv", "mp4", "m4p", "m4v", "mov", "qt", "mng", "mkv", "flv", "f4v", "f4p", "f4a", "f4b", "drc", "avi", "asf", "amv", "3gp", "3g2", "mxf", "m2p", "ps", "m2ts", "mts", "iso", "avchd", "swf"]


def is_dvd_folder(dir_path: Path):
    if dir_path.name.upper() == "VIDEO_TS":
        return True

    bup_exist = False
    ifo_exist = False
    vob_exist = False
    for child in dir_path.iterdir():
        file_format = get_file_format(child)
        if file_format == "bup":
            bup_exist = True
        elif file_format == "ifo":
            ifo_exist = True
        elif file_format == "vob":
            vob_exist = True

    return bup_exist and ifo_exist and vob_exist


def filter_file(file_path: Path, tasks: Tasks):
    file_format = get_file_format(file_path)
    if file_format:
        # if suffix not in VIDEO_SUFFIXES and suffix.lower() in VIDEO_SUFFIXES:
        #     # rename file if it is video and suffix have upper-case letter
        #     suffix = suffix.lower()
        #     file_path = file_path.rename(
        #         file_path.stem + "." + suffix).resolve()
        if file_format in SUPPORT_NORMAL_SUFFIXES:
            tasks.add_task(Task(file_path, "normal"))
            return
        if file_format in SUPPORT_DVD_SUFFIXES:
            tasks.add_task(Task(file_path, "dvd"))
            return
        if file_format in SUPPORT_ISO_SUFFIXES:
            tasks.add_task(Task(file_path, "iso"))
            return
        # if suffix.lower() in SUPPORT_DVD_FOLDER_SUFFIXES:
        #     tasks.add_task([file_path.parent.as_posix(), "dvd_folder", 0])
        #     return "dvd_folder"


def traverse(dir_path: Path, tasks):
    if is_dvd_folder(dir_path):
        tasks.add_task(Task(dir_path, "dvd-folder"))
        return

    for child in dir_path.iterdir():
        if child.is_file():
            filter_file(child, tasks)
        elif child.is_dir():
            traverse(child, tasks)


# filter video file
def filter_video(path: Path = Path(config["input"]), tasks: Tasks = Tasks()) -> Tasks:
    if path.is_file():
        filter_file(path, tasks)
    elif path.is_dir():
        traverse(path, tasks)

    return tasks


# def check_dvd_folder(dir_path):
#     for child in dir_path.iterdir():
#         if child.is_file() and len(child.suffixes) > 0 and child.suffixes[-1][1:].lower() in SUPPORT_DVD_FOLDER_SUFFIXES:
#             return child.parent
#         elif child.is_dir():
#             res = check_dvd_folder(child)
#             if res:
#                 return res
#     return None
