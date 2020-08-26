import subprocess
import logging
from shutil import move
from pathlib import Path
from time import sleep

from .path import get_file_format, rm
from .info import Info
from ..env import config


def ffmpeg_convert(input_path: Path, temp_path: Path):
    info = Info(input_path)
    video_index = info.match_video_codec(config["vc"])
    audio_index = info.match_audio_codec(config["ac"])
    pix_fmt = info.get_pix_fmt()

    # check whether format is same
    if (
        get_file_format(input_path) == config["format"]
        and video_index is not None
        and audio_index is not None
    ):
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
        input_path.resolve().as_posix(),
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
    if video_index is None:
        if config["vc"] == "h264":
            command.extend(
                ["-codec:v", "libx264", "-level:v", "4.2", "-preset", "medium"]
            )
            if config["bit"] == "8":
                if pix_fmt == "yuv420p":
                    command.extend(["-profile:v", "high", "-pix_fmt", "yuv420p"])
                elif pix_fmt == "yuv422p":
                    command.extend(["-profile:v", "high422", "-pix_fmt", "yuv422p"])
                elif pix_fmt == "yuv444p":
                    command.extend(["-profile:v", "high444", "-pix_fmt", "yuv444p"])
            if config["bit"] == "10":
                if pix_fmt == "yuv420p":
                    command.extend(["-profile:v", "high10", "-pix_fmt", "yuv420p10le"])
                elif pix_fmt == "yuv422p":
                    command.extend(["-profile:v", "high422", "-pix_fmt", "yuv422p10le"])
                elif pix_fmt == "yuv444p":
                    command.extend(["-profile:v", "high444", "-pix_fmt", "yuv444p10le"])
        elif config["vc"] == "h265":
            command.extend(
                [
                    "-codec:v",
                    "libx265",
                    "-x265-params",
                    "level-idc=4.2",
                    "-preset",
                    "medium",
                ]
            )
            if config["bit"] == "8":
                if pix_fmt == "yuv420p" or pix_fmt == "yuv422p":
                    command.extend(["-profile:v", "main"])
                elif pix_fmt == "yuv444p":
                    command.extend(["-profile:v", "main444-8"])
            if config["bit"] == "10":
                if pix_fmt == "yuv420p":
                    command.extend(["-profile:v", "main10"])
                elif pix_fmt == "yuv422p":
                    command.extend(["-profile:v", "main422-10"])
                elif pix_fmt == "yuv444p":
                    command.extend(["-profile:v", "main444-10"])
        elif config["vc"] == "vp9":
            command.extend(
                [
                    "-codec:v",
                    "libvpx-vp9",
                    "-b:v",
                    "0",
                    "-level:v",
                    "4.2",
                    "-row-mt",
                    "1",
                ]
            )

        command.extend(["-crf", "18"])
    else:
        command.extend([f"-codec:v:{video_index}", "copy"])

    if audio_index is None:
        if config["ac"] == "aac":
            # -vbr min:1 max:5
            command.extend(["-codec:a", "libfdk_aac", "-vbr", "4"])
        elif config["ac"] == "opus":
            command.extend(["-codec:a", "libopus", "-vbr", "1", "-b:a", "64k"])

    else:
        command.extend([f"-codec:a:{audio_index}", "copy"])

    if config["remove_subtitle"] == "true":
        command.extend(["-sn"])

    command.append(temp_path.resolve().as_posix())
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
        if proc.returncode != 0:
            raise subprocess.SubprocessError(
                "ffmpeg error, check log file for more information."
            )

    # cleanup
    input_path_str = input_path.resolve().as_posix()
    if config["remove_source"] == "true":
        # remove source file
        rm(input_path)
        logging.info(f"Deleted source file {input_path_str}")
    else:
        # rename and keep source file
        input_path.rename(input_path_str + ".source")
        logging.info(f"Renamed source file {input_path_str} to {input_path_str}.source")

    # move target file
    dist_path = input_path.parent.joinpath(temp_path.name)
    move(temp_path, dist_path)
    logging.info(
        f"move temp file {temp_path.absolute().as_posix()} to {dist_path.as_posix()}"
    )


def handbrake_convert(input_path: Path, temp_path: Path):
    # build handbrake run command
    command = [
        "HandBrakeCLI",
        "--format",
        f"av_{config['format']}",
        "-r",
        "60",
        "--pfr",
        "--optimize",
    ]

    if config["vc"] == "h264":
        if config["bit"] == "8":
            command.extend(
                [
                    "--encoder",
                    "x264",
                    "--encoder-profile",
                    "high",
                    "--encoder-level",
                    "4.2",
                ]
            )
        elif config["bit"] == "10":
            command.extend(
                [
                    "--encoder",
                    "x264_10bit",
                    "--encoder-profile",
                    "high10",
                    "--encoder-level",
                    "4.2",
                ]
            )
    elif config["vc"] == "h265":
        if config["bit"] == "8":
            command.extend(
                [
                    "--encoder",
                    "x265",
                    "--encoder-profile",
                    "main",
                    "--encoder-level",
                    "4.2",
                ]
            )
        elif config["bit"] == "10":
            command.extend(
                [
                    "--encoder",
                    "x265_10bit",
                    "--encoder-profile",
                    "main10",
                    "--encoder-level",
                    "4.2",
                ]
            )
    elif config["vc"] == "vp9":
        command.extend(["--encoder", "VP9"])

    command.extend(
        [
            "--quality",
            "18",
            "--encoder-preset",
            "medium",
            #"--align-av",
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
        ["-i", input_path.resolve().as_posix(), "-o", temp_path.resolve().as_posix(),]
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
        if proc.returncode != 0:
            raise subprocess.SubprocessError(
                "HandBrakeCLI error, check log file for more information."
            )

    # cleanup
    input_path_str = input_path.resolve().as_posix()
    if config["remove_source"] == "true":
        # remove source file
        rm(input_path)
        logging.info(f"Deleted source file {input_path_str}")
    else:
        # rename and keep source file
        input_path.rename(input_path_str + ".source")
        logging.info(f"Renamed source file {input_path_str} to {input_path_str}.source")

    # move target file
    dist_path = input_path.parent.joinpath(temp_path.name)
    move(temp_path, dist_path)
    logging.info(
        f"move temp file {temp_path.absolute().as_posix()} to {dist_path.as_posix()}"
    )


# def uncompress(in_path_str, out_path_str):
#     command = ["7z", "e", "-y", "-o" + out_path_str, "-aoa", in_path_str]
#     print(f"Start uncompress: {in_path_str}")
#     res = subprocess.run(command, stdout=subprocess.PIPE)
#     if res.returncode != 0:
#         raise subprocess.SubprocessError(
#             "uncompress error, set debug mode and check log file for more information.")
#     else:
#         print("Complete uncompress.")
