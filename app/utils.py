from json import dump, load
from logging import Formatter, StreamHandler, getLevelName
from os import path


def read_json(relative_path):
    absolute_path = path.join(path.dirname(__file__), relative_path)
    with open(absolute_path, 'r') as f:
        return load(f)


def create_json(data: dict, path: path):
    with open(path, 'w') as f:
        dump(data, f)


def configure_logger(logger, logging_level: str):
    formatter = Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = StreamHandler()
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(getLevelName(logging_level))
