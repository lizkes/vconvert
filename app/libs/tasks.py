import logging
from os import _exit
from typing import List
from enum import Enum

from .time import strf_datetime
from .task import Task, TaskStatus
from ..env import config


class TasksStatus(Enum):
    Waiting = "waiting"
    Running = "running"
    Done = "done"


class Tasks:
    def __init__(
        self, task_list: List[Task] = [], mode=config["mode"], create_time=strf_datetime(),
    ):
        self.create_time = create_time
        self.mode = mode
        self.task_list = list(
            filter(lambda task: task.status != TaskStatus.Error, task_list))
        self.status = TasksStatus.Waiting

    def __str__(self):
        return f"{{create_time: {self.create_time}, mode: {self.mode}, task_list: {self.task_list}}}"

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
            logging.error(
                f"Fail to remove task, index {index} is out of range")
            return

    def execute_task(self, index: str = "0"):
        if self.mode == "transcoding":
            from ..libs import transcoding_filter

            transcoding_filter.filter(tasks=self)
        elif self.mode == "burnsub":
            from ..libs import burnsub_filter

            burnsub_filter.filter(tasks=self)

        if self.status == TasksStatus.Done:
            logging.debug("No new tasks have been added, do nothing")
            return
        elif self.status == TasksStatus.Running:
            logging.error("Tasks are already run, do nothing")
            return
        logging.debug(f"Start Tasks: {self}")
        self.status = TasksStatus.Running

        executed_task_list = []
        if index == "0":
            if executed_task_list != self.task_list:
                executed_task_list = self.task_list.copy()
        else:
            index_list = index.split(",")
            start_index = int(index_list[0])
            end_index = int(index_list[1])
            try:
                executed_task_list.extend(
                    self.task_list[start_index:end_index])
            except IndexError as e:
                logging.error(f"Task execute index exceed: {e}")
                _exit(2)
                return

        for i, task in enumerate(executed_task_list):
            logging.info(
                f"[{i + 1}/{len(executed_task_list)}] Start Task: {task.path.resolve().as_posix()}"
            )

            task.execute()

            logging.info(f"Complete Task {i + 1}.")

        self.status = TasksStatus.Done
