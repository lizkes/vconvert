import os
import sys
import logging
import logging.handlers
from pathlib import Path
from time import sleep

from .env import config
from .libs.task import Tasks
from .libs.filter import filter_video

import os

if __name__ == "__main__":
    current_path = Path(Path(__file__).parent).resolve()

    file_handler = logging.handlers.RotatingFileHandler(
        Path(current_path).joinpath("logs", "run.log"),
        maxBytes=4 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging._nameToLevel.get(config["log_level"], logging.INFO))
    # init logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%y/%m/%d %H:%M:%S",
        handlers=[file_handler, stream_handler],
    )

    Path(config["input"]).mkdir(exist_ok=True)
    Path(config["temp"]).mkdir(exist_ok=True)

    tasks = Tasks()

    while True:
        filter_video(tasks=tasks)
        tasks.execute_task()
        # check tasks every 10 minute
        sleep(10 * 60)
