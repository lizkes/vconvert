import subprocess
import logging
from time import sleep
from shutil import move
from pathlib import Path

from .path import rm
from ..env import config


def burn_sub(input_path: Path, sub_path: Path, sub_format: str, temp_path: Path):
    input_path_str = input_path.resolve().as_posix()

    if sub_format == "srt":
        sub_command = "subtitles"
    elif sub_format == "ass":
        sub_command = "ass"

    command = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-loglevel",
        "info",
        "-i",
        input_path_str,
        "-vf",
        f"{sub_command}={sub_path.resolve().as_posix()}",
        temp_path.resolve().as_posix()
    ]

    logging.debug(f"execute command: {' '.join(command)}")

    # start convert
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
        encoding="utf-8",
        errors="ignore",
    ) as proc:
        log_count = 120
        log_interval = 120
        while True:
            text = proc.stdout.readline().rstrip("\n")
            if text == "":
                if proc.poll() is None:
                    logging.debug("subprocess not exit, sleep 0.5s")
                    sleep(0.5)
                    continue
                else:
                    logging.debug("subprocess exit, done")
                    break
            elif text.startswith("frame="):
                if log_count == log_interval:
                    log_count = 0
                    logging.debug(text)
                else:
                    log_count += 1
            else:
                logging.debug(text)
        if proc.returncode != 0:
            raise subprocess.SubprocessError(
                "ffmpeg error, check log file for more information."
            )

    # cleanup
    if config["remove_source"] == "true":
        # remove source file
        rm(input_path)
        logging.info(f"Deleted source file {input_path_str}")
    else:
        # rename and keep source file
        input_path.rename(input_path_str + ".source")
        logging.info(f"Renamed source file to {input_path_str}.source")

    # move target file
    dist_path = input_path.parent.joinpath(temp_path.name)
    move(temp_path, dist_path)
    logging.info(f"Moved temp file to {dist_path.as_posix()}")

    return Path(dist_path)
