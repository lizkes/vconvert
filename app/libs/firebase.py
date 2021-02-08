import sys
import logging
import pyrebase
from datetime import timedelta

from .time import get_now_datetime, strp_datetime, sleep
from ..env import config


class Firebase:
    def __init__(self, api_key, db_url, project_id, email, password):
        self.api_key = api_key
        self.db_url = db_url
        self.project_id = project_id
        self.email = email
        self.password = password

    def new(self):
        firebase = pyrebase.initialize_app(
            {
                "apiKey": self.api_key,
                "databaseURL": self.db_url,
                "authDomain": f"{self.project_id}.firebaseapp.com",
                "storageBucket": f"{self.project_id}.appspot.com",
            }
        )
        self.auth = firebase.auth()
        self.db = firebase.database()
        self.data = None
        user = self.auth.sign_in_with_email_and_password(self.email, self.password)
        self.id_token = user["idToken"]
        self.refresh_token = user["refreshToken"]
        self.refresh_time = get_now_datetime()

    def is_valid(self):
        return (
            self.api_key
            and self.db_url
            and self.project_id
            and self.email
            and self.password
        )

    def refresh(self):
        now_datetime = get_now_datetime()
        if now_datetime > self.refresh_time + timedelta(minutes=40):
            if now_datetime < self.refresh_time + timedelta(minutes=60):
                user = self.auth.refresh(self.refresh_token)
            else:
                user = self.auth.sign_in_with_email_and_password(
                    self.email, self.password
                )
            self.id_token = user["idToken"]
            self.refresh_token = user["refreshToken"]
            self.refresh_time = now_datetime

    def get(self, path=""):
        self.refresh()
        return self.db.child("vconvert").child(path).get(self.id_token).val()

    def set(self, data, path=""):
        self.refresh()
        return self.db.child("vconvert").child(path).set(data, self.id_token)

    def update(self, data, path=""):
        self.refresh()
        return self.db.child("vconvert").child(path).update(data, self.id_token)

    def remove(self, index, path=""):
        self.refresh()
        return self.db.child("vconvert").child(path).remove(self.id_token)

    def get_seize_data(self):
        retry_number = 0
        while True:
            run_index = self.get("next_index")
            if run_index == -1:
                logging.info("next_index is -1, all tasks done, nothing to do")
                sys.exit(0)

            task_length = self.get("task_length")
            if run_index >= task_length:
                logging.info("run_index >= task_length, all tasks done, nothing to do")
                self.set(-1, "next_index")
                sys.exit(0)

            if run_index + 1 == task_length:
                next_index = -1
            else:
                next_index = run_index + 1
            self.update(
                {
                    "next_index": next_index,
                    f"task_dict/{run_index}/uuid": config["uuid"],
                }
            )
            sleep(3, 5)
            if self.get(f"task_dict/{run_index}/uuid") == config["uuid"]:
                task_obj = self.get(f"task_dict/{run_index}")
                task_obj["index"] = run_index
                return task_obj
            retry_number += 1
            sleep(1, retry_number * 10)

    def update_task(self, task_index, task_obj):
        return self.update(task_obj, f"task_dict/{task_index}")

    def update_append(self, before_data, after_data):
        append_dict = dict()
        for i in range(before_data["task_length"], after_data["task_length"]):
            append_dict[str(i)] = after_data["task_dict"][str(i)]

        if before_data["next_index"] == -1:
            return self.update(
                {
                    "next_index": before_data["task_length"],
                    "task_length": after_data["task_length"],
                    "task_dict": append_dict,
                }
            )
        else:
            return self.update(
                {
                    "task_length": after_data["task_length"],
                    "task_dict": append_dict,
                }
            )

    def remove_unuseful(self, data):
        from .task import TaskStatus

        now_datetime = get_now_datetime()
        sleep_time_delta = timedelta(seconds=int(config["sleep_time"]))
        for index, task in data["task_dict"].items():
            if (
                task["status"] == TaskStatus.Error
                or task["status"] == TaskStatus.Running
            ) and strp_datetime(
                task["activate_time"]
            ) + sleep_time_delta < now_datetime:
                self.remove(index, "task_dict")
