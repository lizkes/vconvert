from os import getenv

config = {
    # only for ffmpeg
    "threads": getenv("threads", None),
    "remove_source": getenv("remove_source", "false"),
    "remove_subtitle": getenv("remove_subtitle", "false"),
    # mp4|mkv
    "format": getenv("format", "mp4"),
    # h264|h265
    "vc": getenv("vc", "h265"),
    # acc|haac
    "ac": getenv("ac", "haac"),
    "input": getenv("vconvert_input", "/vconvert_input"),
    "temp": getenv("vconvert_temp", "/vconvert_temp"),
}
