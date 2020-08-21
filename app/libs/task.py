from pathlib import Path
from typing import List
from os import _exit

from .time import strf_datetime, strf_datetime_pretty
from .convert import ffmpeg_convert, handbrake_convert
from .path import get_output_path, rm
from .log import pdebug, pinfo, perror
from ..env import config


class Task:
    def __init__(self, path: Path, ttype: str, status: str = "waiting"):
        self.path = path
        self.ttype = ttype
        self.status = status

    def execute(self):
        self.status = "runing"
        if self.ttype == "normal":
            ffmpeg_convert(self.path, get_output_path(self.path))
        elif self.ttype == "dvd":
            handbrake_convert(self.path, get_output_path(self.path))
        elif self.ttype == "iso":
            handbrake_convert(self.path, get_output_path(self.path))
        self.status = "success"

class Tasks:
    def __init__(
        self,
        task_list: List[Task] = [],
        create_time: str = strf_datetime(),
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
            if t.path.as_posix() == task.path.as_posix():
                return
        self.task_list.append(task)

    def remove_task(self, index: int = 0):
        try:
            self.task_list.pop(index)
        except IndexError:
            return

    def execute_task(self, index: int = None):
        if self.status == "running":
            pdebug(f"{strf_datetime_pretty()} 任务已在执行，本次执行取消")
            return

        pdebug(f"{strf_datetime_pretty()} 开始执行任务")
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
            pinfo(f"[{i + 1}/{len(executed_task_list)}] {strf_datetime_pretty()}")
            pinfo(f"Task Start: {task.path.as_posix()}")

            try:
                task.execute()
            except KeyboardInterrupt:
                pinfo("\nUser stop tasks")
                rm(get_output_path(task.path))
                task.status = "waiting"
                _exit(1)
            except Exception as e:
                perror(f"[{i + 1}/{len(executed_task_list)}] {strf_datetime_pretty()}")
                perror(e)
                rm(get_output_path(task.path))
                task.status = "error"
                _exit(10)

            self.remove_task(i)
            pinfo(f"[{i + 1}/{len(executed_task_list)}] {strf_datetime_pretty()}")
            pinfo(f"Task Done: {task.path.as_posix()}")

        self.status = "wating"
