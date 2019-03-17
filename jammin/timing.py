import time
from datetime import datetime

now = datetime.now
TIMEREF = datetime.now()


def set_time_reference(value):
    global TIMEREF
    TIMEREF = value


def get_time_reference():
    return TIMEREF


def format_attempt(start, stop):
    reference = get_time_reference()
    after = time.strftime(
        "%H:%M:%S", time.gmtime((stop - reference).total_seconds()))
    took = format((stop - start).total_seconds(), "06.3f")
    return f"[{after}] [{took}]"
