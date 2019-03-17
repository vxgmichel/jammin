
from .data import validate
from .timing import format_attempt, now

ATTEMPTS = {}


def get_attempt(user):
    input_data, expected_lines, startdate = ATTEMPTS[user]
    return expected_lines


def set_attempt(user, input_data, expected_lines, startdate=None):
    if startdate is None:
        startdate = now()
    ATTEMPTS[user] = input_data, expected_lines, startdate


def reset_attempt(user):
    del ATTEMPTS[user]


def validate_attempt(user, output_data, stopdate=None):
    if stopdate is None:
        stopdate = now()
    input_data, expected_lines, startdate = ATTEMPTS.pop(user)
    result = validate(input_data, output_data)
    timing = format_attempt(startdate, stopdate)
    return f"{timing} {result}"
