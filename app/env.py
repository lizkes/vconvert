from os import getenv
from uuid import uuid4

config = {
    "mode": getenv("mode", "transcoding"),
    "sleep_time": getenv("sleep_time", "1800"),
    # only for ffmpeg
    "threads": getenv("threads", "0"),
    "remove_origin": getenv("remove_origin", "false").lower(),
    "remove_subtitle": getenv("remove_subtitle", "false").lower(),
    # mp4|mkv|webm
    "format": getenv("format", "mkv").lower(),
    # h264|h265|vp9
    "vc": getenv("vc", "h264").lower(),
    # aac|opus
    # aac don't support webm
    "ac": getenv("ac", "aac").lower(),
    "crf": getenv("crf", "23"),
    "preset": getenv("preset", "veryfast"),
    "force_convert": getenv("force_convert", "false"),
    "input_dir": getenv("input_dir", "/vconvert").lower(),
    "temp_dir": getenv("temp_dir", "/vconvert").lower(),
    "temp_sub_dir": getenv("temp_sub_dir", "/temp_sub").lower(),
    "log_dir": getenv("log_dir", "/var/log/vconvert").lower(),
    "log_level": getenv("log_level", "INFO").upper(),
    "enable_file_log": getenv("enable_file_log", "true").lower(),
    "uuid": getenv("uuid", uuid4().hex).lower(),
    "fb_api_key": getenv("fb_api_key", ""),
    "fb_project_id": getenv("fb_project_id", ""),
    "fb_db_url": getenv("fb_db_url", ""),
    "fb_email": getenv("fb_email", ""),
    "fb_password": getenv("fb_password", ""),
    "firebase_db": None,
}
