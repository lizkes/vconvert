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
    ]
    SUPPORT_SUB_SUFFIXES = ["ass", "srt"]

    def __init__(self, execute_number=-1):
        self.now_num = 0
        self.need_num = execute_number

    def filter_file(self, file_path, tasks):
        file_format = get_file_format(file_path)
        if file_format in self.SUPPORT_NORMAL_SUFFIXES:
            for sub_suffix in self.SUPPORT_SUB_SUFFIXES:
                sub_file_path = file_path.with_suffix(f".{sub_suffix}")
                if sub_file_path.exists():
                    if tasks.add_task(BurnsubTask(file_path, sub_file_path)):
                        self.now_num += 1
                    return

    def traverse(self, dir_path, tasks):
        for child in dir_path.iterdir():
            if self.now_num == self.need_num:
                return

            if child.is_file():
                self.filter_file(child, tasks)
            elif child.is_dir():
                self.traverse(child, tasks)

    def filte(self, path=Path(config["input_dir"]), tasks=Tasks()):
        if path.is_file():
            self.filter_file(path, tasks)
        elif path.is_dir():
            self.traverse(path, tasks)

        if self.now_num > 0 or self.now_num == self.need_num:
            return True
        else:
            return False


class BothFilter:
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
    ]
    SUPPORT_DVD_SUFFIXES = ["m2ts", "mts", "ts", "avchd"]
    SUPPORT_ISO_SUFFIXES = ["iso"]
    SUPPORT_SUB_SUFFIXES = ["ass", "ssa", "srt"]

    def __init__(self, execute_number=-1):
        self.now_num = 0
        self.need_num = execute_number

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
        if file_format in self.SUPPORT_NORMAL_SUFFIXES:
            for sub_suffix in self.SUPPORT_SUB_SUFFIXES:
                sub_file_path = file_path.with_suffix(f".{sub_suffix}")
                if sub_file_path.exists():
                    if tasks.add_task(BurnsubTask(file_path, sub_file_path)):
                        self.now_num += 1
                    return
            if tasks.add_task(TranscodingTask(file_path, "normal")):
                self.now_num += 1
            return
        if file_format in self.SUPPORT_DVD_SUFFIXES:
            if tasks.add_task(TranscodingTask(file_path, "dvd")):
                self.now_num += 1
            return
        if file_format in self.SUPPORT_ISO_SUFFIXES:
            if tasks.add_task(TranscodingTask(file_path, "iso")):
                self.now_num += 1
            return

    def traverse(self, dir_path, tasks):
        if self.is_dvd_folder(dir_path):
            if tasks.add_task(TranscodingTask(dir_path, "dvd-folder")):
                self.now_num += 1
            return

        for child in dir_path.iterdir():
            if self.now_num == self.need_num:
                return

            if child.is_file():
                self.filter_file(child, tasks)
            elif child.is_dir():
                self.traverse(child, tasks)

    def filte(self, path=Path(config["input_dir"]), tasks=Tasks()):
        if path.is_file():
            self.filter_file(path, tasks)
        elif path.is_dir():
            self.traverse(path, tasks)

        if self.now_num > 0 or self.now_num == self.need_num:
            return True
        else:
            return False


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
    ]
    SUPPORT_DVD_SUFFIXES = ["m2ts", "mts", "ts", "avchd"]
    SUPPORT_ISO_SUFFIXES = ["iso"]

    def __init__(self, execute_number=-1):
        self.now_num = 0
        self.need_num = execute_number

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
        # if suffix not in VIDEO_SUFFIXES and suffix.lower() in VIDEO_SUFFIXES:
        #     # rename file if it is video and suffix have upper-case letter
        #     suffix = suffix.lower()
        #     file_path = file_path.rename(
        #         file_path.stem + "." + suffix)
        if file_format in self.SUPPORT_NORMAL_SUFFIXES:
            if tasks.add_task(TranscodingTask(file_path, "normal")):
                self.now_num += 1
            return
        if file_format in self.SUPPORT_DVD_SUFFIXES:
            if tasks.add_task(TranscodingTask(file_path, "dvd")):
                self.now_num += 1
            return
        if file_format in self.SUPPORT_ISO_SUFFIXES:
            if tasks.add_task(TranscodingTask(file_path, "iso")):
                self.now_num += 1
            return
        # if suffix.lower() in SUPPORT_DVD_FOLDER_SUFFIXES:
        #     tasks.add_task([file_path.parent.as_posix(), "dvd_folder", 0])
        #     return "dvd_folder"

    def traverse(self, dir_path, tasks):
        if self.is_dvd_folder(dir_path):
            if tasks.add_task(TranscodingTask(dir_path, "dvd-folder")):
                self.now_num += 1
            return

        for child in dir_path.iterdir():
            if self.now_num == self.need_num:
                return

            if child.is_file():
                self.filter_file(child, tasks)
            elif child.is_dir():
                self.traverse(child, tasks)

    def filte(self, path=Path(config["input_dir"]), tasks=Tasks()):
        if path.is_file():
            self.filter_file(path, tasks)
        elif path.is_dir():
            self.traverse(path, tasks)

        if self.now_num > 0 or self.now_num == self.need_num:
            return True
        else:
            return False
