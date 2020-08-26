import logging
from pathlib import Path
from typing import List
from os import _exit
from enum import Enum

from .time import strf_datetime
from .convert import ffmpeg_convert, handbrake_convert
from .path import rm, get_temp_path
from ..env import config


class TaskStatus(Enum):
    Waiting = "waiting"
    Running = "running"
    Done = "done"
    Error = "error"


class TasksStatus(Enum):
    Waiting = "waiting"
    Running = "running"
    Done = "done"
    Error = "error"


class Task:
    def __init__(self, path: Path, ttype: str, status=TaskStatus.Waiting):
        self.path = path
        self.ttype = ttype
        self.status = status

    def __str__(self):
        return f"{{path: {self.path}, ttype: {self.ttype}, status: {self.status}}}"

    def execute(self):
        if self.status == TaskStatus.Done:
            logging.error(f"This task is already done, do nothing: {self}")
            return
        elif self.status == TaskStatus.Running:
            logging.error("This task are already run, do nothing: {self}")
            return
        self.status = TaskStatus.Running

        input_path = self.path
        temp_path = get_temp_path(input_path)
        if temp_path is None:
            self.status = TaskStatus.Error
            return

        if self.ttype == "normal":
            ffmpeg_convert(input_path, temp_path)
        elif self.ttype == "dvd":
            handbrake_convert(input_path, temp_path)
        elif self.ttype == "dvd-folder":
            handbrake_convert(input_path, temp_path)
        elif self.ttype == "iso":
            handbrake_convert(input_path, temp_path)
        else:
            logging.error(f"unknown task_type: {self.ttype}")
            self.status = TaskStatus.Error
            return

        self.status = TaskStatus.Done


class Tasks:
    def __init__(
        self, task_list: List[Task] = [], create_time: str = strf_datetime(),
    ):
        temp_task_list: List[Task] = []
        for task in task_list:
            if task.status != TaskStatus.Error:
                temp_task_list.append(task)
        self.task_list = temp_task_list
        self.create_time = create_time
        self.status = TasksStatus.Waiting

    def __str__(self):
        return f"{{create_time: {self.create_time}, task_list: {self.task_list}}}"

    def add_task(self, task: Task):
        # check if task is already exist in task_list
        for t in self.task_list:
            if t.path.resolve().as_posix() == task.path.resolve().as_posix():
                return

        self.task_list.append(task)
        self.status = TasksStatus.Waiting

    def remove_task(self, index: int = 0):
        try:
            self.task_list.pop(index)
        except IndexError:
            return

    def execute_task(self, index: int = None):
        if self.status == TasksStatus.Done:
            logging.debug("No new tasks have been added, do nothing")
            return
        elif self.status == TasksStatus.Running:
            logging.error("Tasks are already run, do nothing")
            return

        logging.debug(f"Start Tasks: {self}")
        self.status = TasksStatus.Running

        executed_task_list = []
        if index:
            try:
                executed_task_list.append(self.task_list[index])
            except IndexError:
                logging.error(f"Task {index} not found")
                self.status = TasksStatus.Error
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
                task.status = TaskStatus.Waiting
                _exit(1)
            except Exception as e:
                logging.fatal(e)
                rm(get_temp_path(task.path))
                task.status = TaskStatus.Error
                _exit(10)

            self.remove_task(i)
            logging.info(f"Complete Task.")

        self.status = TasksStatus.Done
