import logging
from abc import ABC, abstractmethod
from os import _exit
from enum import Enum
from pathlib import Path

from .time import get_now_datetime, strf_datetime, strp_datetime
from .converter import ffmpeg_convert, handbrake_convert, burn_sub
from .path import rm, get_temp_path
from ..env import config


class TaskStatus(str, Enum):
    Waiting = "waiting"
    Running = "running"
    Done = "done"
    Error = "error"


class Task(ABC):
    def __init__(
        self,
        path=None,
        index=0,
        status=TaskStatus.Waiting,
    ):
        self.index = index
        self.activate_time = get_now_datetime()
        self.status = status
        self.uuid = config["uuid"]
        self.path = path

    def __str__(self):
        return (
            f"{{index: {self.index}, activate_time: {strf_datetime(self.activate_time)},"
            f"status: {self.status}, uuid: {self.uuid}, path: {self.path}}}"
        )

    def __repr__(self):
        return self.__str__()

    @abstractmethod
    def from_obj(self, index, obj):
        self.index = index
        self.activate_time = strp_datetime(obj["activate_time"])
        self.status = obj["status"]
        self.uuid = obj["uuid"]
        self.path = Path(obj["path"])

    @abstractmethod
    def to_obj(self):
        obj = {
            "otype": "task",
            "activate_time": strf_datetime(self.activate_time),
            "status": self.status,
            "uuid": self.uuid,
            "path": str(self.path),
        }
        return self.index, obj

    @abstractmethod
    def execute(self):
        if self.status == TaskStatus.Done:
            logging.error(f"This task is already done, do nothing: {self}")
            raise ValueError
        elif self.status == TaskStatus.Running:
            logging.error("This task is already running, do nothing: {self}")
            raise ValueError
        elif self.status == TaskStatus.Error:
            logging.error("This task is error, do nothing: {self}")
            raise ValueError

        self.status = TaskStatus.Running


class TranscodingTask(Task):
    def __init__(
        self,
        path=None,
        ttype=None,
        index=0,
        status=TaskStatus.Waiting,
    ):
        super().__init__(path, index, status)
        self.ttype = ttype

    def __str__(self):
        return (
            f"{{index: {self.index}, activate_time: {strf_datetime(self.activate_time)},"
            f"status: {self.status}, uuid: {self.uuid}, path: {self.path}, type: {self.ttype}}}"
        )

    def from_obj(self, index, obj):
        super().from_obj(index, obj)
        self.ttype = obj["ttype"]

    def to_obj(self):
        index, obj = super().to_obj()
        obj["otype"] = "transcoding"
        obj["ttype"] = self.ttype
        return index, obj

    def execute(self):
        try:
            super().execute()
        except ValueError:
            return

        input_path = self.path
        if not input_path.exists():
            logging.error("can not find input_path: {self}")
            self.status = TaskStatus.Error
            return

        try:
            temp_path = get_temp_path(input_path, config["format"])
        except FileNotFoundError:
            logging.error("can not find temp_path: {self}")
            self.status = TaskStatus.Error
            return

        try:
            if self.ttype == "normal":
                self.path = ffmpeg_convert(input_path, temp_path)
            elif (
                self.ttype == "dvd" or self.ttype == "dvd-folder" or self.ttype == "iso"
            ):
                self.path = handbrake_convert(input_path, temp_path)
            else:
                logging.error(f"unknown task_type: {self.ttype}")
                self.status = TaskStatus.Error
                return
        except KeyboardInterrupt:
            logging.info("\nUser stop tasks")
            rm(temp_path)
            self.status = TaskStatus.Waiting
            _exit(1)
        except Exception as e:
            logging.error(f"unexpected error: {e}")
            rm(temp_path)
            self.status = TaskStatus.Error
            return

        self.status = TaskStatus.Done


class BurnsubTask(Task):
    def __init__(
        self,
        path=None,
        sub_path=None,
        index=0,
        status=TaskStatus.Waiting,
    ):
        super().__init__(path, index, status)
        self.sub_path = sub_path

    def __str__(self):
        return (
            f"{{index: {self.index}, activate_time: {strf_datetime(self.activate_time)},"
            f"status: {self.status}, uuid: {self.uuid}, path: {self.path}, sub_path: {self.sub_path}}}"
        )

    def from_obj(self, index, obj):
        super().from_obj(index, obj)
        self.sub_path = Path(obj["sub_path"])

    def to_obj(self):
        index, obj = super().to_obj()
        obj["otype"] = "burnsub"
        obj["sub_path"] = str(self.sub_path)
        return index, obj

    def execute(self):
        try:
            super().execute()
        except ValueError:
            return

        input_path = self.path
        sub_path = self.sub_path

        if not input_path.exists():
            logging.error("can not find input_path: {self}")
            self.status = TaskStatus.Error
            return
        if not sub_path.exists():
            logging.error("can not find sub_path: {self}")
            self.status = TaskStatus.Error
            return

        try:
            temp_path = get_temp_path(input_path, config["format"])
        except FileNotFoundError:
            logging.error("can not find temp_path: {self}")
            self.status = TaskStatus.Error
            return

        try:
            self.path = burn_sub(input_path, sub_path, temp_path)
        except KeyboardInterrupt:
            logging.info("\nUser stop tasks")
            rm(temp_path)
            self.status = TaskStatus.Waiting
            _exit(1)
        except Exception as e:
            logging.error(f"unexpected error: {e}")
            rm(temp_path)
            self.status = TaskStatus.Error
            return

        self.status = TaskStatus.Done
