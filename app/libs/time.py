from datetime import datetime, timezone, timedelta


def get_now_datetime():
    return datetime.now(timezone(timedelta(hours=8)))


def strf_datetime(time: datetime = get_now_datetime()):
    return datetime.strftime(time, "%Y/%m/%d %H:%M:%S:%f")


def strp_datetime(time_str: str):
    return datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S:%f").replace(
        tzinfo=timezone(timedelta(hours=8))
    )


def strf_time(time: datetime = get_now_datetime()):
    return datetime.strftime(time, "%H%M%S")


def strf_date(time: datetime = get_now_datetime()):
    return datetime.strftime(time, "%y%m%d")
