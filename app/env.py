from os import getenv

config = {
    # only for ffmpeg
    "threads": getenv("vconvert_threads", None),
    "remove_source": getenv("vconvert_remove_source", "false"),
    "remove_subtitle": getenv("vconvert_remove_subtitle", "false"),
    # mp4|mkv
    # mp4比mkv有更快的转码速度，且兼容性更好
    "format": getenv("vconvert_format", "mp4"),
    # 8|10
    "bit": getenv("vconvert_bit", "10"),
    # h264|h265
    "vc": getenv("vconvert_vc", "h264"),
    # aac
    "ac": getenv("vconvert_ac", "aac"),
    "input": getenv("vconvert_input", "/vconvert_input"),
    "temp": getenv("vconvert_temp", "/vconvert_temp"),
}
