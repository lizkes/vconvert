import logging
from enum import Enum
from datetime import timedelta
from time import sleep

from .time import strf_datetime, strp_datetime, get_now_datetime
from .task import Task, TaskStatus
from ..env import config


class TasksStatus(str, Enum):
    NotDone = "not_done"
    Done = "done"


class Tasks:
    def __init__(
        self,
        task_list=[],
        mode=config["mode"],
        firebase_db=None,
    ):
        self.mode = mode
        self.task_list = list(
            filter(lambda task: task.status != TaskStatus.Error, task_list)
        )
        self.firebase_db = firebase_db
        self.status = TasksStatus.NotDone

    def __str__(self):
        return (
            f"{{activate_time: {self.activate_time}, mode: {self.mode},"
            f"status: {self.status}, task_list: {self.task_list}}}"
        )

    def from_obj(self, obj):
        self.activate_time = obj["activate_time"]
        self.mode = obj["mode"]
        self.status = obj["status"]
        self.task_list = obj["task_list"]

    def to_obj(self):
        obj = {
            "activate_time": self.activate_time,
            "mode": self.mode,
            "status": self.status.value,
            "task_list": list(map(lambda x: x.__dict__, self.task_list)),
        }
        return obj

    def save_db(self):
        if self.firebase_db:
            self.firebase_db.set(self.to_obj())

    def get_db(self):
        if self.firebase_db:
            self.from_obj(self.firebase_db.get())

    def add_task(self, task: Task):
        # check if task is already exist in task_list
        for t in self.task_list:
            if t.path.resolve().as_posix() == task.path.resolve().as_posix():
                return False

        if self.firebase_db:
            while True:
                new_task_index = len(self.task_list)
                self.task_list.append(task)
                self.status = TasksStatus.NotDone
                self.save_db()
                sleep(3)
                self.get_db()
                if self.task_list[new_task_index].uuid == config["uuid"]:
                    return True
        else:
            self.task_list.append(task)
            return True

    def remove_task(self, index=0):
        try:
            self.task_list.pop(index)
            return True
        except IndexError:
            logging.error(f"Fail to remove task, index {index} is out of range")
            return False

    def filter_task(self, execute_number=-1):
        if self.mode == "transcoding":
            from .filter import TranscodingFilter

            return TranscodingFilter(execute_number).filte(tasks=self)
        elif self.mode == "burnsub":
            from .filter import BurnsubFilter

            return BurnsubFilter(execute_number).filte(tasks=self)
        elif self.mode == "both":
            from .filter import BothFilter

            return BothFilter(execute_number).filte(tasks=self)

    def execute_task(self, execute_number=-1):
        if self.status == TasksStatus.Done and strp_datetime(
            self.activate_time
        ) + timedelta(seconds=int(config["sleep_time"]) < get_now_datetime()):
            logging.debug("Tasks all done, Nothing to do")
            return

        self.activate_time = strf_datetime()
        if not self.filter_task(execute_number):
            self.status = TasksStatus.Done
            self.save_db()
            logging.debug("Tasks all done, Nothing to do")
            return

        execute_index_list = list()

        for i, task in enumerate(self.task_list):
            if task.uuid == config["uuid"] and task.status == TaskStatus.Waiting:
                execute_index_list.append(i)

        for i, index in enumerate(execute_index_list):
            task = self.task_list[index]
            logging.info(
                f"[{i + 1}/{len(execute_index_list)}] Start Task: {task.path.resolve().as_posix()}"
            )

            task.execute()
            self.save_db()

            logging.info(f"Complete Task {i + 1}.")
