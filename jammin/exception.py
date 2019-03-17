import traceback

import structlog
import pygments.lexers
import pygments.formatters


def log_exception():
    logger = structlog.get_logger()
    text = traceback.format_exc()
    formatter = pygments.formatters.get_formatter_by_name("terminal256")
    lexer = pygments.lexers.get_lexer_by_name("pytb", stripall=True)
    colored = pygments.highlight(text, lexer, formatter)
    logger.warning(f"Unexpected exception:\n{colored}")
