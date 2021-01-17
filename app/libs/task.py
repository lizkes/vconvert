import logging
from abc import ABC, abstractmethod
from os import _exit
from enum import Enum
from pathlib import Path
from .transcoding_convert import ffmpeg_convert, handbrake_convert
from .burnsub_convert import burn_sub
from .path import rm, get_temp_path


class TaskStatus(Enum):
    Waiting = "waiting"
    Running = "running"
    Done = "done"
    Error = "error"


class Task(ABC):
    def __init__(self, path: Path, status=TaskStatus.Waiting):
        self.path = path
        self.status = status

    def __str__(self):
        return f"{{path: {self.path}, status: {self.status}}}"

    def __repr__(self):
        return self.__str__()

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
    def __init__(self, path: Path, ttype: str, status=TaskStatus.Waiting):
        super().__init__(path, status)
        self.ttype = ttype

    def __str__(self):
        return f"{{path: {self.path}, type: {self.ttype}, status: {self.status}}}"

    def execute(self):
        if (super().execute() == 1):
            return

        input_path = self.path
        temp_path = get_temp_path(input_path)
        if temp_path is None:
            logging.error("can not find temp_path: {self}")
            self.status = TaskStatus.Error
            return

        try:
            if self.ttype == "normal":
                self.path = ffmpeg_convert(input_path, temp_path)
            elif self.ttype == "dvd" or self.ttype == "dvd-folder" or self.ttype == "iso":
                self.path = handbrake_convert(input_path, temp_path)
            else:
                logging.error(f"unknown task_type: {self.ttype}")
                self.status = TaskStatus.Error
                return
        except KeyboardInterrupt:
            logging.info("\nUser stop tasks")
            rm(get_temp_path(self.path))
            task.status = TaskStatus.Waiting
            _exit(1)
        except Exception as e:
            logging.error(e)
            rm(get_temp_path(self.path))
            task.status = TaskStatus.Error
            _exit(2)

        self.status = TaskStatus.Done


class BurnsubTask(Task):
    def __init__(self, path: Path, sub_path: Path, ttype: str, status=TaskStatus.Waiting):
        super().__init__(path, status)
        self.sub_path = sub_path
        self.ttype = ttype

    def __str__(self):
        return f"{{path: {self.path}, sub_path: {self.sub_path}, type: {self.ttype}, status: {self.status}}}"

    def execute(self):
        if (super().execute() == 1):
            return

        input_path = self.path
        temp_path = get_temp_path(input_path)
        if temp_path is None:
            logging.error("can not find temp_path: {self}")
            self.status = TaskStatus.Error
            return

        try:
            if self.ttype == "srt" or self.ttype == "ass":
                self.path = burn_sub(
                    input_path, self.sub_path, self.ttype, temp_path)
            else:
                logging.error(f"unknown task_type: {self.ttype}")
                self.status = TaskStatus.Error
                return
        except KeyboardInterrupt:
            logging.info("\nUser stop tasks")
            rm(get_temp_path(self.path))
            task.status = TaskStatus.Waiting
            _exit(1)
        except Exception as e:
            logging.error(e)
            rm(get_temp_path(self.path))
            task.status = TaskStatus.Error
            _exit(2)

        self.status = TaskStatus.Done
