import logging
from datetime import timedelta

from .time import get_now_datetime
from .task import Task, TaskStatus, TranscodingTask, BurnsubTask
from ..env import config


class Tasks:
    def __init__(
        self,
        task_list=[],
        mode=config["mode"],
    ):
        self.mode = mode
        self.next_index = 0
        self.task_list = list(
            filter(lambda task: task.status != TaskStatus.Error, task_list)
        )
        self.task_length = len(self.task_list)

    def __str__(self):
        return (
            f"{{mode: {self.mode}, next_index: {self.next_index}"
            f"task_length: {self.task_length}, task_list: {self.task_list}}}"
        )

    def from_obj(self, obj):
        self.mode = obj["mode"]
        self.next_index = obj["next_index"]
        self.task_length = obj["task_length"]

        task_list = list()
        if "task_dict" in obj:
            for task_index, task_obj in obj["task_dict"].items():
                if task_obj["otype"] == "transcoding":
                    t = TranscodingTask()
                elif task_obj["otype"] == "burnsub":
                    t = BurnsubTask()
                elif task_obj["otype"] == "task":
                    t = Task()
                t.from_obj(task_index, task_obj)
                task_list.append(t)
        self.task_list = task_list

    def from_task_obj(self, task_obj):
        if task_obj["otype"] == "transcoding":
            t = TranscodingTask()
        elif task_obj["otype"] == "burnsub":
            t = BurnsubTask()
        elif task_obj["otype"] == "task":
            t = Task()
        t.from_obj(0, task_obj)
        self.task_list.append(t)

    def to_obj(self):
        task_dict = dict()
        for task in self.task_list:
            task_index, task_obj = task.to_obj()
            task_dict[task_index] = task_obj
        obj = {
            "mode": self.mode,
            "next_index": self.next_index,
            "task_length": self.task_length,
            "task_dict": task_dict,
        }
        return obj

    def add_task(self, task: Task):
        # check if task is already exist in task_list
        for t in self.task_list:
            if str(t.path) == str(task.path):
                if (
                    t.status == TaskStatus.Waiting
                    or t.status == TaskStatus.Done
                    or t.activate_time + timedelta(seconds=int(config["sleep_time"]))
                    > get_now_datetime()
                ):
                    return False
                break

        task.index = self.task_length
        self.task_length += 1
        self.task_list.append(task)
        return True

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

    def execute_remote_task(self):
        task = self.task_list[0]
        logging.debug(f"Start Task: {task.path.as_posix()}")

        task.execute()

        logging.debug(f"Complete Task: {task.path.as_posix()}")

    def execute_local_task(self, execute_number=-1):
        if not self.filter_task(execute_number):
            logging.debug("No new Tasks added, Nothing to do")
            return

        execute_list = self.task_list[0:execute_number]

        for i, task in enumerate(execute_list):
            logging.info(
                f"[{i + 1}/{len(execute_list)}] Start Task: {task.path.as_posix()}"
            )

            task.execute()

            logging.info(
                f"[{i + 1}/{len(execute_list)}] Complete Task: {task.path.as_posix()}"
            )
