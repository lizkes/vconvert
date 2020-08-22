import subprocess
from pathlib import Path

from .json import str_parse_json


class Info:
    def __init__(self, path: Path):
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
        info_obj = str_parse_json(result.stdout.decode("utf-8"))

        self.streams = info_obj["streams"]
        self.format = info_obj["format"]

    def match_video_codec(self, codec_name):
        for stream in self.streams:
            if (
                stream.get("codec_type") == "video"
                and stream.get("codec_name") == codec_name
            ):
                return stream["index"]
        return None

    def match_audio_codec(self, codec_name):
        for stream in self.streams:
            if (
                stream.get("codec_type") == "audio"
                and stream.get("codec_name") == codec_name
            ):
                return stream["index"]
        return None

    # pix_fmt: yuv420p yuv422p yuv444p yuvj420p yuvj422p yuvj444p yuv420p10le yuv422p10le yuv444p10le
    def get_pix_fmt(self):
        for stream in self.streams:
            if stream.get("codec_type") == "video":
                pix_fmt = stream.get("pix_fmt", "yuv420p")
                if (
                    pix_fmt == "yuv422p"
                    or pix_fmt == "yuvj422p"
                    or pix_fmt == "yuv422p10le"
                ):
                    return "yuv422p"
                elif (
                    pix_fmt == "yuv444p"
                    or pix_fmt == "yuvj444p"
                    or pix_fmt == "yuv444p10le"
                ):
                    return "yuv444p"
                else:
                    return "yuv420p"
        return "yuv420p"
