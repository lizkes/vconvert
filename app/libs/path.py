import shutil
import logging
from pathlib import Path
from time import sleep

from ..env import config


def change_parent_dir(input_path, before_parent, after_parent):
    return Path(after_parent).joinpath(input_path.relative_to(before_parent))


def get_temp_path(input_path, format):
    def change_file_format(input_path, format):
        if input_path.is_file():
            suffix = input_path.suffix
            if suffix:
                return Path(f"{input_path.as_posix()[:-(len(suffix))]}.{format}.vctemp")
        elif input_path.is_dir():
            return Path(f"{input_path.as_posix()}.{format}.vctemp")
        else:
            return input_path

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
            f"input_path is neither a file nor a folder: {input_path.as_posix()}"
        )
        raise FileNotFoundError


def get_file_format(input_path):
    return input_path.suffix[1:]


def add_suffix(input_path, suffix):
    return Path(f"{input_path.as_posix()}.{suffix}")


def remove_suffix(input_path, suffix):
    return input_path.with_suffix(input_path.suffix.rstrip(suffix))


def rm(paths):
    def try_to_rm(path):
        try_count = 10
        while try_count > 0:
            try:
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                        logging.debug(f"{path} is folder, removed")
                    elif path.is_file():
                        path.unlink()
                        logging.debug(f"{path} is file, removed")
                    else:
                        logging.warn(f"{path} is neither file nor folder, can't delete.")
                else:
                    logging.info(f"{path} is not exist, can't delete.")
                break
            except PermissionError as e:
                try_count -= 1
                logging.error("\n", e, "\nRetry after one second")
                sleep(1)

    if type(paths) == list:
        for path in paths:
            try_to_rm(path)
    else:
        try_to_rm(paths)
