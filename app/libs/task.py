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
        status=TaskStatus.Waiting,
    ):
        self.activate_time = get_now_datetime()
        self.uuid = config["uuid"]
        self.path = path
        self.status = status

    def __str__(self):
        return (
            f"{{activate_time: {strf_datetime(self.activate_time)}, uuid: {self.uuid},"
            f"status: {self.status}, path: {str(self.path)}}}"
        )

    def __repr__(self):
        return self.__str__()

    def update_db_task(self):
        if config["firebase_db"]:
            config["firebase_db"].update(self.uuid, self.to_obj())

    def set_status(self, status):
        self.status = status
        if status == TaskStatus.Done or status == TaskStatus.Error:
            self.update_db_task()

    @abstractmethod
    def from_obj(self, uuid, obj):
        self.activate_time = strp_datetime(obj["activate_time"])
        self.uuid = uuid
        self.path = Path(obj["path"])
        self.status = obj["status"]

    @abstractmethod
    def to_obj(self):
        obj = {
            "activate_time": strf_datetime(self.activate_time),
            "otype": "task",
            "path": str(self.path),
            "status": self.status,
        }
        return obj

    @abstractmethod
    def execute(self):
        if self.status == TaskStatus.Done:
            logging.error(f"This task is already done, do nothing: {self}")
            return 1
        elif self.status == TaskStatus.Running:
            logging.error("This task is already running, do nothing: {self}")
            return 1
        elif self.status == TaskStatus.Error:
            logging.error("This task is error, do nothing: {self}")
            return 1

        self.status = TaskStatus.Running


class TranscodingTask(Task):
    def __init__(
        self,
        path=None,
        ttype=None,
        status=TaskStatus.Waiting,
    ):
        super().__init__(path, status)
        self.ttype = ttype

    def __str__(self):
        return f"{{path: {self.path}, type: {self.ttype}, status: {self.status}, uuid: {self.uuid}}}"

    def from_obj(self, uuid, obj):
        super().from_obj(uuid, obj)
        self.ttype = obj["ttype"]

    def to_obj(self):
        obj = super().to_obj()
        obj["otype"] = "transcoding"
        obj["ttype"] = self.ttype
        return obj

    def execute(self):
        if super().execute() == 1:
            return

        input_path = self.path
        temp_path = get_temp_path(input_path, config["format"])
        if temp_path is None:
            logging.error("can not find temp_path: {self}")
            self.set_status(TaskStatus.Error)
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
                self.set_status(TaskStatus.Error)
                return
        except KeyboardInterrupt:
            logging.info("\nUser stop tasks")
            rm(temp_path)
            self.set_status(TaskStatus.Waiting)
            _exit(1)
        except Exception as e:
            logging.error(f"unexpected error: {e}")
            rm(temp_path)
            self.set_status(TaskStatus.Error)
            _exit(2)

        self.set_status(TaskStatus.Done)


class BurnsubTask(Task):
    def __init__(
        self,
        path=None,
        sub_path=None,
        status=TaskStatus.Waiting,
    ):
        super().__init__(path, status)
        self.sub_path = sub_path

    def __str__(self):
        return f"{{path: {self.path}, sub_path: {self.sub_path}, status: {self.status}, uuid: {self.uuid}}}"

    def from_obj(self, uuid, obj):
        super().from_obj(uuid, obj)
        self.sub_path = Path(obj["sub_path"])

    def to_obj(self):
        obj = super().to_obj()
        obj["otype"] = "burnsub"
        obj["sub_path"] = str(self.sub_path)
        return obj

    def execute(self):
        if super().execute() == 1:
            return

        input_path = self.path
        temp_path = get_temp_path(input_path, config["format"])
        if temp_path is None:
            logging.error("can not find temp_path: {self}")
            self.set_status(TaskStatus.Error)
            return

        try:
            self.path = burn_sub(input_path, self.sub_path, temp_path)
        except KeyboardInterrupt:
            logging.info("\nUser stop tasks")
            rm(temp_path)
            self.set_status(TaskStatus.Waiting)
            _exit(1)
        except Exception as e:
            logging.error(f"unexpected error: {e}")
            rm(temp_path)
            self.set_status(TaskStatus.Error)
            _exit(2)

        self.set_status(TaskStatus.Done)
