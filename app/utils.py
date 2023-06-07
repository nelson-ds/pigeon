from json import dump, load
from logging import Formatter, StreamHandler, getLevelName


def read_json(json_path_str: str):
    with open(json_path_str, 'r') as f:
        return load(f)


def create_json(path: str, data: dict):
    with open(path, 'w') as f:
        dump(data, f)


def configure_logger(logger, logging_level: str):
    formatter = Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = StreamHandler()
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(getLevelName(logging_level))
