import logging


RESET = "\033[0m"
COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[35m",
}


class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = COLORS.get(record.levelname, RESET)
        record.levelname = f"{color}{record.levelname}{RESET}"
        return super().format(record)


class StandardFormatter(logging.Formatter):
    pass
