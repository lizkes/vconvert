from pathlib import Path

from .task import BurnsubTask, TranscodingTask
from .tasks import Tasks
from .path import get_file_format
from ..env import config


class BurnsubFilter:
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

    def __init__(self):
        if config["execute_index"] != "0":
            index_list = config["execute_index"].split(",")
            self.need_find = int(index_list[1]) - int(index_list[0])
        else:
            self.need_find = -1
        self.find_count = 0

    def filter_file(self, file_path, tasks):
        file_format = get_file_format(file_path)
        if file_format in self.SUPPORT_NORMAL_SUFFIXES:
            srt_file_path = Path(file_path.with_suffix(".srt"))
            if srt_file_path.exists():
                tasks.add_task(BurnsubTask(file_path, srt_file_path, "srt"))
                self.find_count += 1
                return

            ass_file_path = Path(file_path.with_suffix(".ass"))
            if ass_file_path.exists():
                tasks.add_task(BurnsubTask(file_path, ass_file_path, "ass"))
                self.find_count += 1
                return

    def traverse(self, dir_path, tasks):
        for child in dir_path.iterdir():
            if self.find_count == self.need_find:
                return

            if child.is_file():
                self.filter_file(child, tasks)
            elif child.is_dir():
                self.traverse(child, tasks)

            if self.find_count == self.need_find:
                return

    def filte(self, path=Path(config["input_dir"]), tasks=Tasks()):
        if path.is_file():
            self.filter_file(path, tasks)
        elif path.is_dir():
            self.traverse(path, tasks)


class TranscodingFilter:
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

    def __init__(self):
        if config["execute_index"] != "0":
            index_list = config["execute_index"].split(",")
            self.need_find = int(index_list[1]) - int(index_list[0])
        else:
            self.need_find = -1
        self.find_count = 0

    def is_dvd_folder(self, dir_path):
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

    def filter_file(self, file_path, tasks):
        file_format = get_file_format(file_path)
        if file_format:
            # if suffix not in VIDEO_SUFFIXES and suffix.lower() in VIDEO_SUFFIXES:
            #     # rename file if it is video and suffix have upper-case letter
            #     suffix = suffix.lower()
            #     file_path = file_path.rename(
            #         file_path.stem + "." + suffix).resolve()
            if file_format in self.SUPPORT_NORMAL_SUFFIXES:
                tasks.add_task(TranscodingTask(file_path, "normal"))
                self.find_count += 1
                return
            if file_format in self.SUPPORT_DVD_SUFFIXES:
                tasks.add_task(TranscodingTask(file_path, "dvd"))
                self.find_count += 1
                return
            if file_format in self.SUPPORT_ISO_SUFFIXES:
                tasks.add_task(TranscodingTask(file_path, "iso"))
                self.find_count += 1
                return
            # if suffix.lower() in SUPPORT_DVD_FOLDER_SUFFIXES:
            #     tasks.add_task([file_path.parent.as_posix(), "dvd_folder", 0])
            #     return "dvd_folder"

    def traverse(self, dir_path, tasks):
        if self.is_dvd_folder(dir_path):
            tasks.add_task(TranscodingTask(dir_path, "dvd-folder"))
            self.find_count += 1
            return

        for child in dir_path.iterdir():
            if self.find_count == self.need_find:
                return

            if child.is_file():
                self.filter_file(child, tasks)
            elif child.is_dir():
                self.traverse(child, tasks)

            if self.find_count == self.need_find:
                return

    def filte(self, path=Path(config["input_dir"]), tasks=Tasks()):
        if path.is_file():
            self.filter_file(path, tasks)
        elif path.is_dir():
            self.traverse(path, tasks)
