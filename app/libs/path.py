import shutil
import logging
from pathlib import Path
from time import sleep

from ..env import config


def get_temp_path(input_path, format):
    if input_path.is_file():
        return Path(config["temp_dir"]).joinpath(
            change_file_format(input_path, format).relative_to(config["input_dir"])
        )
    elif input_path.is_dir():
        if input_path.name.upper() == "VIDEO_TS":
            return Path(config["temp_dir"]).joinpath(
                input_path.parent.relative_to(config["input_dir"]),
                f"{input_path.parent.name}.{format}.vctemp",
            )
        else:
            return Path(config["temp_dir"]).joinpath(
                change_file_format(input_path, format).relative_to(config["input_dir"])
            )
    else:
        logging.error(
            f"input_path is neither a file nor a folder: {input_path.resolve().as_posix()}"
        )
        return None


def get_file_format(input_path):
    if input_path.is_file():
        suffixes = input_path.suffixes
        if len(suffixes) > 0:
            file_format = suffixes[-1][1:].lower()
            if len(file_format) > 0:
                return file_format
    return None


def change_file_format(input_path, format):
    if input_path.is_file():
        suffix = input_path.suffix
        if suffix:
            return Path(f"{input_path.as_posix()[:-(len(suffix))]}.{format}.vctemp")
    elif input_path.is_dir():
        return Path(f"{input_path.as_posix()}.{format}.vctemp")
    else:
        return input_path


def rm(path):
    try_count = 10
    while try_count > 0:
        try:
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.is_file():
                    path.unlink()
                else:
                    logging.warn(f"{path} is not dir or file, can't delete.")
            else:
                logging.info(f"{path} is not exist, can't delete.")
            break
        except PermissionError as e:
            try_count -= 1
            logging.debug("\n", e, "\nRetry after one second")
            sleep(1)
