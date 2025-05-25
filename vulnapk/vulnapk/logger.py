import logging
import sys


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        message = super().format(record)
        return f"{log_color}{message}{self.RESET}"


def init(level: int = logging.INFO) -> None:
    logger = logging.getLogger("vulnapk")
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = ColoredFormatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def logi(message: str) -> None:
    logging.getLogger("vulnapk").info(message)

def logd(message: str) -> None:
    logging.getLogger("vulnapk").debug(message)

def logw(message: str) -> None:
    logging.getLogger("vulnapk").warning(message)

def loge(message: str) -> None:
    logging.getLogger("vulnapk").error(message)