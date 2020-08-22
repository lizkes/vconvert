import shutil
from os import _exit
from logging import debug, warn, fatal
from pathlib import Path
from time import sleep

from ..env import config


def get_output_path(input_path: Path):
    if input_path.is_file():
        return Path(
            Path(config["output"]).joinpath(
                change_file_format(input_path, config["format"]).relative_to(
                    config["input"]
                )
            )
        )
    elif input_path.is_dir():
        if input_path.name.upper() == "VIDEO_TS":
            return Path(
                Path(config["output"]).joinpath(
                    input_path.parent.relative_to(config["input"]),
                    f"{input_path.parent.name}.{config['format']}",
                )
            )
        else:
            fatal("输出路径是不支持的文件夹: ", input_path.as_posix())
            _exit(1)
    else:
        fatal("输出路径既不是文件也不是文件夹: ", input_path.as_posix())
        _exit(1)


def get_file_format(input_path: Path):
    if input_path.is_file():
        suffixes = input_path.suffixes
        if len(suffixes) > 0:
            file_format = suffixes[-1][1:].lower()
            if len(file_format) > 0:
                return file_format
    return None


def change_file_format(input_path: Path, format: str):
    if input_path.is_file():
        suffix = input_path.suffix
        if suffix:
            return Path(f"{input_path.as_posix()[:-(len(suffix)-1)]}{format}")
    return input_path


def rm(path: Path):
    try_count = 10
    while try_count > 0:
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
            try_count -= 1
            debug("\n", e, "\nRetry after one second")
            sleep(1)
