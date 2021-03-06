import sys
import logging
from pathlib import Path
from datetime import timedelta

from .time import get_now_datetime
from .path import rm
from .task import Task, TaskStatus, TranscodingTask, BurnsubTask, TaskReturnCode
from .check import check_upload_success
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
        if "task_list" in obj:
            for task_index, task_obj in enumerate(obj["task_list"]):
                if task_obj["otype"] == "transcoding":
                    t = TranscodingTask()
                elif task_obj["otype"] == "burnsub":
                    t = BurnsubTask()
                elif task_obj["otype"] == "task":
                    t = Task()
                t.from_obj(task_index, task_obj)
                task_list.append(t)
        self.task_list = task_list

    def from_task_obj(self, index, task_obj):
        if task_obj["otype"] == "transcoding":
            t = TranscodingTask()
        elif task_obj["otype"] == "burnsub":
            t = BurnsubTask()
        elif task_obj["otype"] == "task":
            t = Task()
        t.from_obj(index, task_obj)
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
            "task_list": task_dict,
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

        file_size = task.path.stat().st_size
        if file_size < int(config["limit_size"]):
            task.index = self.task_length
            self.task_length += 1
            self.task_list.append(task)
            return True
        else:
            logging.debug(f"file size {file_size} is over limit_size")
            logging.debug(f"cannot add task: {str(task.path)}")
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

    def execute_remote_task(self):
        task = self.task_list[0]
        logging.debug(f"Start Task: {str(task.path)}")
        logging.info(f"Current index: {task.index}")

        result = task.execute()

        if result == TaskReturnCode.Complete:
            if not check_upload_success(Path(config["rclone_log_path"])):
                logging.ERROR(
                    f"Output file cannot upload successfully: {str(task.path)}"
                )
                task.update_status(TaskStatus.Error)
                sys.exit(1)
            elif config["remove_origin"] == "true":
                logging.debug(f"Output file upload successfully: {str(task.path)}")
                rm(task.origin_paths)
            else:
                logging.debug(f"Output file upload successfully: {str(task.path)}")

        logging.debug(f"Complete Task: {str(task.path)}")

        return result

    def execute_local_task(self, execute_number=-1):
        if not self.filter_task(execute_number):
            logging.debug("No new Tasks added, Nothing to do")
            return

        execute_list = self.task_list[0:execute_number]

        for i, task in enumerate(execute_list):
            logging.info(f"[{i + 1}/{len(execute_list)}] Start Task: {str(task.path)}")

            task.execute()

            logging.info(
                f"[{i + 1}/{len(execute_list)}] Complete Task: {str(task.path)}"
            )
