import shutil
from logging import debug, warn
from pathlib import Path
from time import sleep

from ..env import config


def get_output_path(input_path: Path):
    return Path(
        Path.joinpath(config["output"], input_path.relative_to(config["input"]))
    )


def get_file_format(input_path: Path):
    if input_path.is_file():
        suffixes = input_path.suffixes
        if len(suffixes) > 0:
            file_format = suffixes[-1][1:].lower()
            if len(file_format) > 0:
                return file_format
    return None


def rm(path: Path):
    try_time = 10
    while try_time > 0:
        try:
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.is_file():
                    path.unlink()
                else:
                    warn(f"{path} is not dir or file, can't delete.")
            else:
                warn(f"{path} is not exist, can't delete.")
            break
        except PermissionError as e:
            try_time -= 1
            debug("\n", e, "\nRetry after one second")
            sleep(1)
