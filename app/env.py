from os import getenv

config = {
    # only for ffmpeg
    "threads": getenv("threads", None),
    "remove_source": getenv("remove_source", "false"),
    "remove_subtitle": getenv("remove_subtitle", "false"),
    # mp4|mkv
    "format": getenv("format", "mp4"),
    # h264|h265
    "vc": getenv("vc", "h264"),
    # acc|haac
    "ac": getenv("ac", "aac"),
    "input": getenv("vconvert_input", "/vconvert_input"),
    "output": getenv("vconvert_output", "/vconvert_output"),
}
