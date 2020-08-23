import logging
from pathlib import Path
from typing import List
from os import _exit

from .time import strf_datetime
from .convert import ffmpeg_convert, handbrake_convert
from .path import rm, get_temp_path
from ..env import config


class Task:
    def __init__(self, path: Path, ttype: str, status: str = "waiting"):
        self.path = path
        self.ttype = ttype
        self.status = status

    def __str__(self):
        return f"{{path: {self.path}, ttype: {self.ttype}, status: {self.status}}}"

    def execute(self):
        self.status = "runing"

        input_path = self.path
        temp_path = get_temp_path(input_path)

        if self.ttype == "normal":
            ffmpeg_convert(input_path, temp_path)
        elif self.ttype == "dvd":
            handbrake_convert(input_path, temp_path)
        elif self.ttype == "dvd-folder":
            handbrake_convert(input_path, temp_path)
        elif self.ttype == "iso":
            handbrake_convert(input_path, temp_path)
        else:
            logging.fatal(f"unknown task_type: {self.ttype}")
            _exit(10)

        self.status = "success"


class Tasks:
    def __init__(
        self, task_list: List[Task] = [], create_time: str = strf_datetime(),
    ):
        temp_task_list: List[Task] = []
        for task in task_list:
            if task.status != "error":
                temp_task_list.append(task)
        self.task_list = temp_task_list
        self.create_time = create_time
        self.status = "waiting"

    def __str__(self):
        return f"{{create_time: {self.create_time}, task_list: {self.task_list}}}"

    def add_task(self, task: Task):
        for t in self.task_list:
            if t.path.resolve().as_posix() == task.path.resolve().as_posix():
                return
        self.task_list.append(task)

    def remove_task(self, index: int = 0):
        try:
            self.task_list.pop(index)
        except IndexError:
            return

    def execute_task(self, index: int = None):
        if self.status == "running":
            logging.error("Tasks are already run")
            return

        logging.debug(f"Start Tasks: {self}")
        self.status = "running"

        executed_task_list = []
        if index:
            try:
                executed_task_list.append(self.task_list[index])
            except IndexError:
                self.status = "wating"
                return
        else:
            executed_task_list = self.task_list.copy()

        for i, task in enumerate(executed_task_list):
            logging.info(
                f"[{i + 1}/{len(executed_task_list)}] Start Task: {task.path.resolve().as_posix()}"
            )

            try:
                task.execute()
            except KeyboardInterrupt:
                logging.info("\nUser stop tasks")
                rm(get_temp_path(task.path))
                task.status = "waiting"
                _exit(1)
            except Exception as e:
                logging.fatal(e)
                rm(get_temp_path(task.path))
                task.status = "error"
                _exit(10)

            self.remove_task(i)
            logging.info(f"Complete Task.")

        self.status = "wating"
