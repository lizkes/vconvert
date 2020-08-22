import subprocess
import logging
from pathlib import Path
from time import sleep
from shlex import quote

from .path import get_file_format, rm
from .info import get_video_json, match_codec
from ..env import config


def ffmpeg_convert(input_path: Path, output_path: Path):
    info = get_video_json(input_path)
    video_index = match_codec(info, "video", config["vc"])
    audio_index = match_codec(info, "audio", config["ac"])

    # check whether format is same
    if get_file_format(input_path) == config["format"] and video_index is not None and audio_index is not None:
        logging.info("same format, nothing to do.")
        return

    # build ffmpeg run command
    # sn mean not subtitle stream
    command = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-loglevel",
        "info",
        "-i",
        quote(input_path.resolve().as_posix()),
        "-f",
        config["format"],
        "-movflags",
        "+faststart",
    ]

    if config["threads"]:
        command.extend(["-threads", config["threads"]])

    if video_index is None:
        if config["vc"] == "h264":
            command.extend(["-codec:v", "libx264"])
        elif config["vc"] == "h265":
            command.extend(["-codec:v", "libx265"])

        command.extend(
            ["-crf", "20", "-profile:v", "high", "-level", "4.1", "-preset", "medium"]
        )

        if config["format"] == "mp4":
            command.extend(["-pix_fmt", "yuv420p"])
    else:
        command.extend([f"-codec:v:{video_index}", "copy"])

    if audio_index is None:
        if config["ac"] == "aac":
            command.extend(["-codec:a", "aac", "-q:a", "2"])
        elif config["ac"] == "haac":
            command.extend(["-codec:a", "libfdk_aac", "-vbr", "5"])
    else:
        command.extend([f"-codec:a:{audio_index}", "copy"])

    if config["remove_subtitle"] == "true":
        command.extend(["-sn"])

    command.append(quote(output_path.resolve().as_posix()))
    logging.debug(" ".join(command))

    # get video duration
    # try:
    #     video_duration = int(info["format"]["duration"][:-7])
    # except KeyError:
    #     logging.debug(f"can't get duration from {input_path.as_posix()}, skip...")
    #     return
    # start convert
    with subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
        encoding="utf-8",
        check=True,
    ) as proc:
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
            logging.debug(text)
            print(text)
        # if proc.returncode != 0:
        #     raise subprocess.SubprocessError(
        #         "ffmpeg error, check log file for more information.")


def handbrake_convert(input_path: Path, output_path: Path):
    # build handbrake run command
    command = [
        "HandBrakeCLI",
        "--format",
        f"av_{config['format']}",
        "--optimize",
        "--vfr",
    ]

    if config["vc"] == "h264":
        command.extend(["--encoder", "x264"])
    elif config["vc"] == "h265":
        command.extend(["--encoder", "x265"])

    command.extend(
        [
            "--quality",
            "20",
            "--encoder-preset",
            "medium",
            "--encoder-profile",
            "high",
            "--align-av",
            "--encoder-level",
            "4.1",
            "--keep-display-aspect",
            "--auto-anamorphic",
            "--maxHeight",
            "1080",
            "--maxWidth",
            "1920",
            "--main-feature",
            "--first-audio",
            "--aencoder",
            "copy",
            "--aq",
            "10",
        ]
    )

    if config["ac"] == "aac":
        command.extend(["--audio-fallback", "ca_aac"])
    elif config["ac"] == "haac":
        command.extend(["--audio-fallback", "ca_haac"])

    if config["remove_subtitle"] != "true":
        command.extend(
            [
                "--all-subtitles",
                #  "--subtitle-lang-list", "eng,chi"
            ]
        )

    command.extend(["-i", quote(input_path.resolve().as_posix()), "-o", quote(output_path.resolve().as_posix())])
    logging.debug(" ".join(command))

    with subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
        encoding="utf-8",
        check=True,
    ) as proc:
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
            logging.debug(text)
            print(text)
        # if proc.returncode != 0:
        #     raise subprocess.SubprocessError(
        #         "HandBrakeCLI error, check log file for more information.")


# def uncompress(in_path_str, out_path_str):
#     command = ["7z", "e", "-y", "-o" + out_path_str, "-aoa", in_path_str]
#     print(f"Start uncompress: {in_path_str}")
#     res = subprocess.run(command, stdout=subprocess.PIPE)
#     if res.returncode != 0:
#         raise subprocess.SubprocessError(
#             "uncompress error, set debug mode and check log file for more information.")
#     else:
#         print("Complete uncompress.")
