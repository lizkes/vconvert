import subprocess

from .json import str_parse_json


class Info:
    def __init__(self, path):
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
        self.video_stream_index = 0
        self.audio_stream_index = 0

    def match_video_codec(self, codec_name, codec_bit):
        stream_index = 0
        for stream in self.streams:
            if stream.get("codec_type") == "video":
                if (
                    stream.get("codec_name") == codec_name
                    and stream.get("bits_per_raw_sample") == codec_bit
                ):
                    self.video_stream_index = stream_index
                    return stream_index
                else:
                    stream_index += 1
        return None

    def match_audio_codec(self, codec_name):
        stream_index = 0
        for stream in self.streams:
            if stream.get("codec_type") == "audio":
                if stream.get("codec_name") == codec_name:
                    self.audio_stream_index = stream_index
                    return stream_index
                else:
                    stream_index += 1
        return None

    # pix_fmt: yuv420p yuv422p yuv444p yuvj420p yuvj422p yuvj444p yuv420p10le yuv422p10le yuv444p10le
    def get_pix_fmt(self):
        stream_index = 0
        for stream in self.streams:
            if stream.get("codec_type") == "video":
                if stream_index == self.video_stream_index:
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
                else:
                    stream_index += 1
        return "yuv420p"
