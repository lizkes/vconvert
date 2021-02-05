import logging
from enum import Enum
from datetime import timedelta
from time import sleep

from .time import strf_datetime, strp_datetime, get_now_datetime
from .task import Task, TaskStatus, TranscodingTask, BurnsubTask
from ..env import config


class TasksStatus(str, Enum):
    NotDone = "not_done"
    Done = "done"


class Tasks:
    def __init__(
        self,
        task_list=[],
        mode=config["mode"],
    ):
        self.mode = mode
        self.task_list = list(
            filter(lambda task: task.status != TaskStatus.Error, task_list)
        )
        self.status = TasksStatus.NotDone
        self.activate_time = strf_datetime()

    def __str__(self):
        return (
            f"{{activate_time: {self.activate_time}, mode: {self.mode},"
            f"status: {self.status}, task_list: {self.task_list}}}"
        )

    def from_obj(self, obj):
        self.activate_time = obj["activate_time"]
        self.mode = obj["mode"]
        self.status = obj["status"]

        task_list = list()
        if "task_dict" in obj:
            for task_uuid, task_obj in obj["task_dict"].items():
                if task_obj["otype"] == "transcoding":
                    t = TranscodingTask()
                elif task_obj["otype"] == "burnsub":
                    t = BurnsubTask()
                elif task_obj["otype"] == "task":
                    t = Task()
                t.from_obj(task_uuid, task_obj)
                task_list.append(t)
        self.task_list = task_list

    def to_obj(self):
        task_dict = dict()
        for task in self.task_list:
            task_dict[task.uuid] = task.to_obj()
        obj = {
            "activate_time": self.activate_time,
            "mode": self.mode,
            "status": self.status,
            "task_dict": task_dict,
        }
        return obj

    def save_db(self):
        if config["firebase_db"]:
            config["firebase_db"].set(self.to_obj())

    def update_db(self, task):
        if config["firebase_db"]:
            config["firebase_db"].update(task.uuid, task.to_obj())

    def get_db(self):
        if config["firebase_db"]:
            self.from_obj(config["firebase_db"].get())

    def add_task(self, task: Task):
        # check if task is already exist in task_list
        for t in self.task_list:
            if str(t.path) == str(task.path):
                return False

        if config["firebase_db"]:
            self.task_list.append(task)
            self.status = TasksStatus.NotDone
            self.update_db(task)
            sleep(3)
            self.get_db()
            for t in self.task_list:
                if str(t.path) == str(task.path) and t.uuid == task.uuid:
                    return True
            return False
        else:
            self.task_list.append(task)
            self.status = TasksStatus.NotDone
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

        if not self.filter_task(execute_number):
            self.status = TasksStatus.Done
            self.activate_time = strf_datetime()
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
                f"[{i + 1}/{len(execute_index_list)}] Start Task: {task.path.as_posix()}"
            )

            task.execute()
            self.update_db(task)

            logging.info(f"Complete Task {i + 1}.")
