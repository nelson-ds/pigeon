import logging
import logging.config
from json import dump, load

from pythonjsonlogger import jsonlogger

logger = None


class CustomLogger():

    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, log_record, record, message_dict):
            super().add_fields(log_record, record, message_dict)

    def __init__(self):
        self.logging_config = None
        self.logger = None
        self._apply()

    def _apply(self):
        format_dev = "%(name)s %(message)s"
        format_prod = "%(asctime)s %(process)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)s %(message)s"

        self.logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": self.CustomJsonFormatter,
                    "format": format_dev,
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z"
                }
            },
            "handlers": {
                "console": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "root": {
                "handlers": ["console"],
                "level": "DEBUG"
            }
        }

        logging.config.dictConfig(self.logging_config)
        self.logger = logging.getLogger(__name__)


def read_json(json_path_str: str):
    with open(json_path_str, 'r') as f:
        return load(f)


def create_json(path: str, data: dict):
    with open(path, 'w') as f:
        dump(data, f)


def file_to_dict(file_path: str, delimiter: str):
    file_dict = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split(delimiter)
            file_dict[key.strip()] = value.strip()
    return file_dict


custom_logger = CustomLogger()
logger = custom_logger.logger
