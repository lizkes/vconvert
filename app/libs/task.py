from pathlib import Path
from typing import List
from os import _exit
from logging import debug, info, error, fatal

from .time import strf_datetime
from .convert import ffmpeg_convert, handbrake_convert
from .path import get_output_path, rm
from ..env import config


class Task:
    def __init__(self, path: Path, ttype: str, status: str = "waiting"):
        self.path = path
        self.ttype = ttype
        self.status = status

    def execute(self):
        self.status = "runing"

        input_path = self.path
        output_path = get_output_path(input_path)

        if self.ttype == "normal":
            ffmpeg_convert(input_path, output_path)
        elif self.ttype == "dvd":
            handbrake_convert(input_path, output_path)
        elif self.ttype == "dvd-folder":
            handbrake_convert(input_path, output_path)
        elif self.ttype == "iso":
            handbrake_convert(input_path, output_path)
        else:
            fatal(f"未知的task_type: {self.ttype}")
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
            debug("任务已在执行，本次执行取消")
            return

        debug("开始执行任务")
        self.status = "running"

        executed_task_list = []
        if index:
            try:
                executed_task_list.append(self.task_list[index])
            except IndexError:
                self.status = "wating"
                return
        else:
            executed_task_list = self.task_list

        for i, task in enumerate(executed_task_list):
            info(f"[{i + 1}/{len(executed_task_list)}]")
            info(f"Task Start: {task.path.resolve().as_posix()}")

            try:
                task.execute()
            except KeyboardInterrupt:
                info("\nUser stop tasks")
                rm(get_output_path(task.path))
                task.status = "waiting"
                _exit(1)
            except Exception as e:
                fatal(f"[{i + 1}/{len(executed_task_list)}]")
                fatal(e)
                rm(get_output_path(task.path))
                task.status = "error"
                _exit(10)

            self.remove_task(i)
            info(f"[{i + 1}/{len(executed_task_list)}]")
            info(f"Task Done: {task.path.resolve().as_posix()}")

        self.status = "wating"
