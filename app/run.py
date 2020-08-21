import os
import logging
from time import sleep

from .libs.task import Tasks
from .libs.filter import filter_video

import os

if __name__ == '__main__':
    # filter input dir
    tasks = Tasks()

    while(True):
        filter_video(tasks)
        tasks.execute_task()
        sleep(1 * 60 * 60)