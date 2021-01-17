import os
import sys
import pprint
import logging
import logging.handlers
from pathlib import Path, PurePath
from time import sleep

from .env import config
from .libs.tasks import Tasks

import os

if __name__ == "__main__":
    current_path = PurePath(__file__).parent
    log_dir = Path(current_path.parent.joinpath("logs"))
    log_path = log_dir.joinpath("run.log")
    if not log_dir.exists():
        log_dir.mkdir()
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=10 * 1024 * 1024, backupCount=1, encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging._nameToLevel.get(
        config["log_level"], logging.INFO))
    # init logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%y/%m/%d %H:%M:%S",
        handlers=[file_handler, stream_handler],
    )

    Path(config["input"]).mkdir(exist_ok=True)
    Path(config["temp"]).mkdir(exist_ok=True)

    # 输出环境变量
    logging.debug(f"\n{pprint.pformat(config, indent=2)}")

    tasks = Tasks()

    if config["execute_index"] == "0":
        while True:
            tasks.execute_task()
            sleep(float(config["sleep_time"]))
    else:
        index_list = config["execute_index"].split(",")
        start_index = int(index_list[0])
        end_index = int(index_list[1])
        tasks.execute_task(start_index, end_index)
