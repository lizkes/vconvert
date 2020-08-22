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

    # init logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%y/%m/%d %H:%M:%S",
        handlers=[
            logging.handlers.RotatingFileHandler(
                Path.joinpath(current_path, "logs", "run.log"),
                maxBytes=1 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8"
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )

    Path(config["input"]).mkdir(exist_ok=True)
    Path(config["output"]).mkdir(exist_ok=True)
    
    tasks = Tasks()

    while True:
        filter_video(tasks=tasks)
        tasks.execute_task()
        sleep(1 * 60 * 60)
