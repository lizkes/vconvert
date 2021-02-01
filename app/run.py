import sys
import pprint
import logging
import logging.handlers
from pathlib import Path, PurePath
from time import sleep

from .env import config
from .libs.tasks import Tasks
from .libs.firebase import FirebaseDB

if __name__ == "__main__":
    Path(config["input_dir"]).mkdir(exist_ok=True)
    Path(config["temp_dir"]).mkdir(exist_ok=True)
    Path(config["log_dir"]).mkdir(exist_ok=True)

    current_path = PurePath(__file__).parent
    file_handler = logging.handlers.RotatingFileHandler(
        Path(config["log_dir"]).joinpath("run.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=1,
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

    db = FirebaseDB(
        config["fb_api_key"],
        config["fb_project_id"],
        config["fb_db_url"],
        config["fb_email"],
        config["fb_password"],
    )
    if db.is_valid():
        db.new()
        data = db.get()
        tasks = Tasks(firebase_db=db)
        if data:
            tasks.from_obj(data)

        tasks.execute_task(execute_number=1)
    else:
        # 输出环境变量
        logging.debug(f"\n{pprint.pformat(config, indent=2)}")

        tasks = Tasks()
        while True:
            tasks.execute_task()
            sleep(float(config["sleep_time"]))
