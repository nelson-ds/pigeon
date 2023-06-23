from json import dump, load
from logging import Formatter, StreamHandler, getLevelName, getLogger

logger = None


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


def configure_logger():
    logger = getLogger(__name__)
    formatter = Formatter('%(asctime)s %(levelname)s %(message)s\n', datefmt='%Y-%m-%d %H:%M:%S')
    handler = StreamHandler()
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(getLevelName('DEBUG'))
    return logger


logger = configure_logger()
