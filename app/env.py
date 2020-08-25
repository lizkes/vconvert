from os import getenv

config = {
    # only for ffmpeg
    "threads": getenv("threads", None),
    "remove_source": getenv("remove_source", "false"),
    "remove_subtitle": getenv("remove_subtitle", "false"),
    # mp4|mkv|webm
    "format": getenv("format", "mp4"),
    # h264|h265|vp9
    "vc": getenv("vc", "h264"),
    # aac|opus
    # aac don't support webm
    "ac": getenv("ac", "aac"),
    # 8|10
    # don't support vp9
    "bit": getenv("bit", "8"),
    "input": getenv("input", "/vconvert_input"),
    "temp": getenv("temp", "/vconvert_temp"),
    "log_level": getenv("log_level", "INFO"),
}
