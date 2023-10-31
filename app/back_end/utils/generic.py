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
        self.logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": self.CustomJsonFormatter,
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "root": {
                "handlers": ["console"],
                "level": "INFO"
            }
        }

        logging.config.dictConfig(self.logging_config)
        self.logger = logging.getLogger(__name__)
        self.change_formatter()
        self.change_logging_level()

    def change_formatter(self, minimized=True):
        format_minimized = "%(levelname)s %(name)s %(message)s"
        format_default = "%(asctime)s %(process)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)s %(message)s"
        if minimized:
            self.logging_config['formatters']['json']['format'] = format_minimized
        else:
            self.logging_config['formatters']['json']['format'] = format_default
        logging.config.dictConfig(self.logging_config)

    def change_logging_level(self, root_logging_level=logging.INFO):
        self.logging_config['root']['level'] = root_logging_level
        logging.config.dictConfig(self.logging_config)


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
