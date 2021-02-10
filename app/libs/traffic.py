import time
import logging

# bytes pretty-printing
UNITS_MAPPING = [
    (1 << 50, " PB"),
    (1 << 40, " TB"),
    (1 << 30, " GB"),
    (1 << 20, " MB"),
    (1 << 10, " KB"),
    (1, (" byte", " bytes")),
]


def pretty_size(bytes, units=UNITS_MAPPING):
    """Get human-readable file sizes.
    simplified version of https://pypi.python.org/pypi/hurry.filesize/
    """
    for factor, suffix in units:
        if bytes >= factor:
            break
    amount = int(bytes / factor)

    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix


def transmissionrate(dev, direction, timestep):
    """Return the transmisson rate of a interface under linux
    dev: devicename
    direction: rx (received) or tx (sended)
    timestep: time to measure in seconds
    """
    path = f"/sys/class/net/{dev}/statistics/{direction}_bytes"
    with open(path, "r") as f1:
        bytes_before = int(f1.read())
    time.sleep(timestep)
    with open(path, "r") as f2:
        bytes_after = int(f2.read())
    return (bytes_after - bytes_before) / timestep


def check_traffic_in_github_action():
    byterate = transmissionrate("eth0", "tx", 10) / 10
    logging.debug(f"upload byterate: {pretty_size(byterate)}")
    while byterate > 16 * 1024:  # 16KB/s
        byterate = transmissionrate("eth0", "tx", 10) / 10
        print(f"upload byterate: {pretty_size(byterate)}")
