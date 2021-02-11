import time
import logging


def search(file_path):
    with open(file_path, mode="r", encoding="utf-8") as f:
        content = f.read()
    start_upload_number = content.count("starting upload")
    upload_success_number = content.count("upload succeeded")
    logging.debug(f"start_upload_number: {start_upload_number}")
    logging.debug(f"upload_success_number: {upload_success_number}")
    return start_upload_number == upload_success_number


# 1000 seconds
def check_upload_success(log_path):
    if log_path.is_file():
        for count in range(0, 50):
            if search(log_path) is True:
                # waiting for rename
                time.sleep(3)
                return True
            time.sleep(20)
        return False
