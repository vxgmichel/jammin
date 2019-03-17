

import contextvars


CONFIG = contextvars.ContextVar("Configuration")


def get_configuration():
    return CONFIG.get()


def set_configuration(namespace):
    CONFIG.set(namespace)
