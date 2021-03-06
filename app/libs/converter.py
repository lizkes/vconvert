import subprocess
import logging
from time import sleep
from shutil import move
from pathlib import Path
from shlex import quote

from .path import change_parent_dir, get_file_format
from .encode import file_encoding, to_utf8
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
        return False

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
        "-max_muxing_queue_size",
        "1024",
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
                ["-codec:v", "libx264", "-level:v", "4.1", "-preset", config["preset"]]
            )
            if video_bit == "8":
                command.extend(["-profile:v", "high", "-pix_fmt", "yuv420p"])
            elif video_bit == "10":
                command.extend(["-profile:v", "high10", "-pix_fmt", "yuv420p10le"])
        elif config["vc"] == "h265":
            command.extend(["-codec:v", "libx265", "-preset", config["preset"]])
            if video_bit == "8":
                command.extend(["-profile:v", "main", "-pix_fmt", "yuv420p"])
            elif video_bit == "10":
                command.extend(["-profile:v", "main10", "-pix_fmt", "yuv420p10le"])
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
            elif video_bit == "10":
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
        log_count = 50
        log_interval = 58
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
                    logging.info(text)
                else:
                    log_count += 1
            else:
                logging.debug(text)
        if proc.returncode != 0:
            raise subprocess.SubprocessError(
                "ffmpeg error, check debug level log for more information."
            )

    # rename and keep origin file
    origin_input_path = Path(f"{input_path_str}.origin")
    input_path.rename(origin_input_path)
    logging.debug(f"Renamed origin file to {str(origin_input_path)}")

    # move target file
    dist_path = input_path.parent.joinpath(temp_path.name.rstrip("vctemp").rstrip("."))
    move(temp_path, dist_path)
    logging.debug(f"Moved temp file to {str(dist_path)}")

    return Path(dist_path), [origin_input_path]


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
            config["preset"],
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
        log_count = 50
        log_interval = 58
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
                    logging.info(text)
                else:
                    log_count += 1
            else:
                logging.debug(text)
        if proc.returncode != 0:
            raise subprocess.SubprocessError(
                "handbrake error, check debug level log for more information."
            )

    # rename and keep origin file
    origin_input_path = Path(f"{input_path_str}.origin")
    input_path.rename(origin_input_path)
    logging.debug(f"Renamed origin file to {str(origin_input_path)}")

    # move target file
    dist_path = input_path.parent.joinpath(temp_path.name.rstrip("vctemp").rstrip("."))
    move(temp_path, dist_path)
    logging.debug(f"Moved temp file to {str(dist_path)}")

    return Path(dist_path), [origin_input_path]


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
    sub_path_format = sub_path.suffix[1:]
    sub_file_encoding = file_encoding(sub_path)

    if sub_path_format == "srt":
        ffmpeg_sub_command = "subtitles"
    elif sub_path_format == "ass" or sub_path_format == "ssa":
        ffmpeg_sub_command = "ass"
    else:
        logging.error(f"Unrecognized subtitle format: {sub_path_format}")
        return

    if sub_file_encoding == "UTF-8":
        temp_sub_path = sub_path
        logging.debug("sub file encoding is UTF-8, no need to convert")
    else:
        temp_sub_path = change_parent_dir(
            sub_path, config["input_dir"], config["temp_sub_dir"]
        )
        logging.debug(f"sub file encoding is {sub_file_encoding}, convert to UTF-8...")
        to_utf8(sub_file_encoding, sub_path, temp_sub_path)

    command = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-loglevel",
        "info",
        "-i",
        input_path_str,
        "-vf",
        f"{ffmpeg_sub_command}={quote(temp_sub_path.as_posix())}",
        "-movflags",
        "+faststart",
        "-max_muxing_queue_size",
        "1024",
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
        command.extend(
            ["-codec:v", "libx264", "-level:v", "4.1", "-preset", config["preset"]]
        )
        if video_bit == "8":
            command.extend(["-profile:v", "high", "-pix_fmt", "yuv420p"])
        elif video_bit == "10":
            command.extend(["-profile:v", "high10", "-pix_fmt", "yuv420p10le"])
    elif config["vc"] == "h265":
        command.extend(
            [
                "-codec:v",
                "libx265",
                "-preset",
                config["preset"],
            ]
        )
        if video_bit == "8":
            command.extend(["-profile:v", "main", "-pix_fmt", "yuv420p"])
        elif video_bit == "10":
            command.extend(["-profile:v", "main10", "-pix_fmt", "yuv420p10le"])
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
        elif video_bit == "10":
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
        log_count = 50
        log_interval = 58
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
                    logging.info(text)
                else:
                    log_count += 1
            else:
                logging.debug(text)
        if proc.returncode != 0:
            raise subprocess.SubprocessError(
                "ffmpeg error, check debug level log for more information."
            )

    # rename and keep origin file
    origin_input_path = Path(f"{input_path_str}.origin")
    origin_sub_path = Path(f"{sub_path_str}.origin")
    input_path.rename(origin_input_path)
    logging.debug(f"Renamed origin file to {str(origin_input_path)}")
    sub_path.rename(origin_sub_path)
    logging.debug(f"Renamed origin file to {str(origin_sub_path)}")

    # move target file
    dist_path = input_path.parent.joinpath(temp_path.name.rstrip("vctemp").rstrip("."))
    move(temp_path, dist_path)
    logging.debug(f"Moved temp file to {dist_path.as_posix()}")

    return dist_path, [origin_input_path, origin_sub_path]
