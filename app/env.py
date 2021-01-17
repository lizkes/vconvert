from os import getenv

config = {
    "mode": getenv("mode", "transcoding"),
    "sleep_time": getenv("sleep_time", "600"),
    "execute_index": getenv("execute_index", "0"),
    # only for ffmpeg
    "threads": getenv("threads", "0"),
    "remove_source": getenv("remove_source", "false").lower(),
    "remove_subtitle": getenv("remove_subtitle", "false").lower(),
    # mp4|mkv|webm
    "format": getenv("format", "mp4").lower(),
    # h264|h265|vp9
    "vc": getenv("vc", "h264").lower(),
    # aac|opus
    # aac don't support webm
    "ac": getenv("ac", "aac").lower(),
    # 8|10 don't support for vp9
    "bit": getenv("bit", "8"),
    "input": getenv("input", "/vconvert_input").lower(),
    "temp": getenv("temp", "/vconvert_temp").lower(),
    "log_level": getenv("log_level", "INFO").upper(),
}
