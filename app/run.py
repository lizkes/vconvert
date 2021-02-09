import sys
import atexit
import pprint
import logging
import logging.handlers
from pathlib import Path
from time import sleep

from .env import config, g_var
from .libs.path import rm
from .libs.task import TaskReturnCode
from .libs.tasks import Tasks
from .libs.firebase import Firebase

if __name__ == "__main__":
    # init logging
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging._nameToLevel.get(config["log_level"], logging.INFO))
    if config["enable_file_log"] == "true":
        file_handler = logging.handlers.RotatingFileHandler(
            Path(config["log_dir"]).joinpath("run.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=1,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%y/%m/%d %H:%M:%S",
            handlers=[file_handler, stream_handler],
        )
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%y/%m/%d %H:%M:%S",
            handlers=[stream_handler],
        )

    db = None
    if config["storage"] == "firebase":
        db = Firebase(
            config["fb_api_key"],
            config["fb_db_url"],
            config["fb_project_id"],
            config["fb_email"],
            config["fb_password"],
        )
        if db.is_valid():
            db.new()
            g_var["db"] = db

    if config["role"] == "indexer":
        if g_var["db"]:
            tasks = Tasks()
            data = g_var["db"].get()
            if data:
                tasks.from_obj(data)
                if tasks.filter_task():
                    g_var["db"].update_append(data, tasks.to_obj())
                    g_var["db"].remove_unuseful(data)
                else:
                    logging.debug("no task added, do nothing")
            else:
                tasks.filter_task()
                g_var["db"].set(tasks.to_obj())

        sys.exit(0)
    elif config["role"] == "runner":
        Path(config["input_dir"]).mkdir(parents=True, exist_ok=True)
        Path(config["temp_dir"]).mkdir(parents=True, exist_ok=True)
        Path(config["log_dir"]).mkdir(parents=True, exist_ok=True)

        # set exit job
        def exit_handler():
            if config["mode"] == "both" or config["mode"] == "burnsub":
                rm(Path(config["temp_sub_dir"]))
                logging.debug(f"removed temp sub dir: {config['temp_sub_dir']}")

        atexit.register(exit_handler)

        if g_var["db"]:
            # firebase storage
            DoNothingCount = 0
            while DoNothingCount < config["max_do_nothing"]:
                index, task_obj = g_var["db"].get_seize_data()
                tasks = Tasks()
                tasks.from_task_obj(index, task_obj)
                return_code = tasks.execute_remote_task()

                if return_code == TaskReturnCode.DoNothing:
                    DoNothingCount += 1
                else:
                    break
            sys.exit(0)
        else:
            # none storage
            logging.debug(f"\n{pprint.pformat(config, indent=2)}")

            tasks = Tasks()
            while True:
                tasks.execute_local_task()
                sleep(config["sleep_time"])
