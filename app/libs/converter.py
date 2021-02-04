import subprocess
import logging
from time import sleep
from shutil import move
from pathlib import Path
from shlex import quote

from .path import get_file_format, rm
from .encode import is_utf16, utf16_to_utf8
from .info import Info
from ..env import config


def ffmpeg_convert(input_path, temp_path):
    info = Info(input_path)
    video_index = info.match_video_codec(config["vc"])
    video_bit = info.get_bit()
    audio_index = info.match_audio_codec(config["ac"])
    input_path_str = input_path.as_posix()

    # check whether format is same
    if (
        get_file_format(input_path) == config["format"]
        and video_index is not None
        and audio_index is not None
        and config["force_convert"] == "false"
    ):
        logging.info("same format, nothing to do.")
        return input_path

    # build ffmpeg run command
    # sn mean not subtitle stream
    command = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-loglevel",
        "info",
        "-i",
        input_path_str,
        "-movflags",
        "+faststart",
    ]

    if config["format"] == "mkv":
        command.extend(["-f", "matroska"])
    elif config["format"] == "mp4":
        command.extend(["-f", "mp4"])
    elif config["format"] == "webm":
        command.extend(["-f", "webm"])

    if config["threads"] != "0":
        command.extend(["-threads", config["threads"]])

    # pix_fmt: yuv420p yuv422p yuv444p yuvj420p yuvj422p yuvj444p yuv420p10le yuv422p10le yuv444p10le
    # for x265 doc, see https://x265.readthedocs.io/en/default/cli.html#profile-level-tier
    if video_index is None or config["force_convert"] == "true":
        if config["vc"] == "h264":
            command.extend(
                ["-codec:v", "libx264", "-level:v", "4.1", "-preset", "medium"]
            )
            if video_bit == "8":
                command.extend(["-profile:v", "high", "-pix_fmt", "yuv420p"])
            if video_bit == "10":
                command.extend(["-profile:v", "high10", "-pix_fmt", "yuv420p10le"])
        elif config["vc"] == "h265":
            command.extend(
                [
                    "-codec:v",
                    "libx265",
                    "-preset",
                    "medium",
                ]
            )
            if video_bit == "8":
                command.extend(["-profile:v", "main"])
            if video_bit == "10":
                command.extend(["-profile:v", "main10"])
        elif config["vc"] == "vp9":
            command.extend(
                [
                    "-codec:v",
                    "libvpx-vp9",
                    # https://trac.ffmpeg.org/wiki/Encode/VP9#constantq
                    "-b:v",
                    "0",
                    # https://trac.ffmpeg.org/wiki/Encode/VP9#rowmt
                    "-row-mt",
                    "1",
                ]
            )
            if video_bit == "8":
                command.extend(["-pix_fmt", "yuv420p"])
            if video_bit == "10":
                command.extend(["-pix_fmt", "yuv420p10le"])

        command.extend(["-crf", config["crf"]])
    else:
        command.extend([f"-codec:v:{video_index}", "copy"])

    if audio_index is None or config["force_convert"] == "true":
        if config["ac"] == "aac":
            # -vbr min:1 max:5
            command.extend(["-codec:a", "libfdk_aac", "-vbr", "5"])
        elif config["ac"] == "opus":
            command.extend(["-codec:a", "libopus", "-vbr", "1", "-b:a", "96K"])
    else:
        command.extend([f"-codec:a:{audio_index}", "copy"])

    if config["remove_subtitle"] == "true":
        command.extend(["-sn"])

    command.append(temp_path.as_posix())
    logging.debug(f"execute command: {' '.join(command)}")

    # get video duration
    # try:
    #     video_duration = int(info["format"]["duration"][:-7])
    # except KeyError:
    #     logging.debug(f"can't get duration from {input_path.as_posix()}, skip...")
    #     return

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
    if config["remove_origin"] == "true":
        # remove origin file
        rm(input_path)
        logging.info(f"Deleted origin file {input_path_str}")
    else:
        # rename and keep origin file
        input_path.rename(input_path_str + ".origin")
        logging.info(f"Renamed origin file to {input_path_str}.origin")

    # move target file
    dist_path = input_path.parent.joinpath(temp_path.name.rstrip("vctemp").rstrip("."))
    move(temp_path, dist_path)
    logging.info(f"Moved temp file to {dist_path.as_posix()}")

    return Path(dist_path)


def handbrake_convert(input_path, temp_path):
    input_path_str = input_path.as_posix()

    # build handbrake run command
    command = [
        "handbrake",
        "--format",
        f"av_{config['format']}",
        "-r",
        "60",
        "--pfr",
        "--optimize",
    ]

    if config["vc"] == "h264":
        command.extend(
            [
                "--encoder",
                "x264",
                "--encoder-profile",
                "high",
                "--encoder-level",
                "4.1",
            ]
        )
    elif config["vc"] == "h265":
        command.extend(
            [
                "--encoder",
                "x265",
                "--encoder-profile",
                "main",
            ]
        )
    elif config["vc"] == "vp9":
        command.extend(["--encoder", "VP9"])

    command.extend(
        [
            "--quality",
            config["crf"],
            "--encoder-preset",
            "medium",
            # "--align-av",
            "--auto-anamorphic",
            "--keep-display-aspect",
            # "--maxHeight",
            # "1080",
            # "--maxWidth",
            # "1920",
            "--main-feature",
            "--first-audio",
        ]
    )

    if config["ac"] == "aac":
        command.extend(["--aencoder", "copy:aac", "--audio-fallback", "ca_haac"])
    elif config["ac"] == "opus":
        command.extend(["--aencoder", "opus"])
    command.extend(["--aq", "8"])

    if config["remove_subtitle"] != "true":
        command.extend(
            [
                "--all-subtitles",
                #  "--subtitle-lang-list", "eng,chi"
            ]
        )

    command.extend(
        [
            "-i",
            input_path_str,
            "-o",
            temp_path.as_posix(),
        ]
    )
    logging.debug(f"execute command: {' '.join(command)}")

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
                "handbrake error, check log file for more information."
            )

    # cleanup
    if config["remove_origin"] == "true":
        # remove origin file
        rm(input_path)
        logging.info(f"Deleted origin file {input_path_str}")
    else:
        # rename and keep origin file
        input_path.rename(input_path_str + ".origin")
        logging.info(f"Renamed origin file to {input_path_str}.origin")

    # move target file
    dist_path = input_path.parent.joinpath(temp_path.name.rstrip("vctemp").rstrip("."))
    move(temp_path, dist_path)
    logging.info(f"Moved temp file to {dist_path.as_posix()}")

    return Path(dist_path)


# def uncompress(in_path_str, out_path_str):
#     command = ["7z", "e", "-y", "-o" + out_path_str, "-aoa", in_path_str]
#     print(f"Start uncompress: {in_path_str}")
#     res = subprocess.run(command, stdout=subprocess.PIPE)
#     if res.returncode != 0:
#         raise subprocess.SubprocessError(
#             "uncompress error, set debug mode and check log file for more information.")
#     else:
#         print("Complete uncompress.")


def burn_sub(input_path, sub_path, temp_path):
    info = Info(input_path)
    info.match_video_codec(config["vc"])
    video_bit = info.get_bit()
    audio_index = info.match_audio_codec(config["ac"])
    input_path_str = input_path.as_posix()
    sub_path_str = sub_path.as_posix()

    if is_utf16(sub_path):
        logging.info("sub file is utf-16, start convert to utf-8...")
        utf16_to_utf8(sub_path, sub_path)

    command = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-loglevel",
        "info",
        "-i",
        input_path_str,
        "-vf",
        f"subtitles={quote(sub_path_str)}",
        "-movflags",
        "+faststart",
    ]

    if config["format"] == "mkv":
        command.extend(["-f", "matroska"])
    elif config["format"] == "mp4":
        command.extend(["-f", "mp4"])
    elif config["format"] == "webm":
        command.extend(["-f", "webm"])

    if config["threads"] != "0":
        command.extend(["-threads", config["threads"]])

    # pix_fmt: yuv420p yuv422p yuv444p yuvj420p yuvj422p yuvj444p yuv420p10le yuv422p10le yuv444p10le
    # for x265 doc, see https://x265.readthedocs.io/en/default/cli.html#profile-level-tier
    if config["vc"] == "h264":
        command.extend(["-codec:v", "libx264", "-level:v", "4.1", "-preset", "medium"])
        if video_bit == "8":
            command.extend(["-profile:v", "high", "-pix_fmt", "yuv420p"])
        if video_bit == "10":
            command.extend(["-profile:v", "high10", "-pix_fmt", "yuv420p10le"])
    elif config["vc"] == "h265":
        command.extend(
            [
                "-codec:v",
                "libx265",
                "-preset",
                "medium",
            ]
        )
        if video_bit == "8":
            command.extend(["-profile:v", "main"])
        if video_bit == "10":
            command.extend(["-profile:v", "main10"])
    elif config["vc"] == "vp9":
        command.extend(
            [
                "-codec:v",
                "libvpx-vp9",
                # https://trac.ffmpeg.org/wiki/Encode/VP9#constantq
                "-b:v",
                "0",
                # https://trac.ffmpeg.org/wiki/Encode/VP9#rowmt
                "-row-mt",
                "1",
            ]
        )
        if video_bit == "8":
            command.extend(["-pix_fmt", "yuv420p"])
        if video_bit == "10":
            command.extend(["-pix_fmt", "yuv420p10le"])

    command.extend(["-crf", config["crf"]])

    if audio_index is None or config["force_convert"] == "true":
        if config["ac"] == "aac":
            # -vbr min:1 max:5
            command.extend(["-codec:a", "libfdk_aac", "-vbr", "5"])
        elif config["ac"] == "opus":
            command.extend(["-codec:a", "libopus", "-vbr", "1", "-b:a", "96K"])
    else:
        command.extend([f"-codec:a:{audio_index}", "copy"])

    command.append(temp_path.as_posix())
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
    if config["remove_origin"] == "true":
        # remove origin file
        rm(input_path)
        logging.info(f"Deleted origin file {input_path_str}")
        rm(sub_path)
        logging.info(f"Deleted origin file {sub_path_str}")
    else:
        # rename and keep origin file
        input_path.rename(f"{input_path_str}.origin")
        logging.info(f"Renamed origin file to {input_path_str}.origin")
        sub_path.rename(f"{sub_path_str}.origin")
        logging.info(f"Renamed origin file to {sub_path_str}.origin")

    # move target file
    dist_path = input_path.parent.joinpath(temp_path.name.rstrip("vctemp").rstrip("."))
    move(temp_path, dist_path)
    logging.info(f"Moved temp file to {dist_path.as_posix()}")

    return Path(dist_path)
