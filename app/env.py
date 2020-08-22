from os import getenv

config = {
    # only for ffmpeg
    "threads": getenv("vconvert_threads", None),
    "remove_source": getenv("vconvert_remove_source", "false"),
    "remove_subtitle": getenv("vconvert_remove_subtitle", "false"),
    # mp4|mkv|webm
    "format": getenv("vconvert_format", "mp4"),
    # 8|10
    # don't support vp9
    "bit": getenv("vconvert_bit", "8"),
    # h264|h265|vp9
    "vc": getenv("vconvert_vc", "h264"),
    # aac|opus
    # aac don't support webm
    "ac": getenv("vconvert_ac", "aac"),
    "input": getenv("vconvert_input", "/vconvert_input"),
    "temp": getenv("vconvert_temp", "/vconvert_temp"),
}
