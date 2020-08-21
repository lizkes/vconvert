import subprocess
from pathlib import Path

from .json import str_parse_json


def get_video_json(path: Path):
    result = subprocess.run(
        [
            "ffprobe",
            "-hide_banner",
            "-loglevel",
            "quiet",
            "-show_format",
            "-show_streams",
            "-print_format",
            "json",
            path.as_posix(),
        ],
        capture_output=True,
        check=True,
    )
    return str_parse_json(result.stdout.decode("utf-8"))


def match_codec(info, codec_type, codec_name):
    match_index = None
    for item in info["streams"]:
        if item["codec_type"] == codec_type:
            if item["codec_name"] == codec_name:
                match_index = item["index"]
                break
    return match_index
