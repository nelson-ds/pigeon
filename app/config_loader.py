from logging import getLogger
from os import getenv, path
from pprint import pformat

from dotenv import load_dotenv
from utils import create_json, read_json

logger = getLogger('uvicorn')


class ConfigLoader:
    def __init__(self):
        self.env = self._get_environment()
        self.combined_configs = self._combine_all_configs()
        self.all_configs = self._prep_configs_for_runtime()
        self._print_configs()

    def _get_environment(self):
        dotenv_path = path.join(path.dirname(__file__), 'configs', '.env')
        load_dotenv(dotenv_path)
        return getenv('ENVIRONMENT')

    def _combine_all_configs(self):
        configs = read_json(f'configs/config.{self.env}.json')
        secrets = read_json(f'configs/secrets/.secrets.{self.env}.json')
        twilio_secrets = read_json(f'configs/secrets/.twilio-cli.{self.env}/config.json')
        combined_configs = {**configs, **secrets, **twilio_secrets}
        return combined_configs

    def _prep_configs_for_runtime(self):
        all_configs_file = path.join(path.dirname(__file__), 'configs/secrets', f'.runtime_secrets_and_configs.{self.env}.json')
        create_json(self.combined_configs, all_configs_file)
        return read_json(all_configs_file)

    def _print_configs(self):
        all_configs_formatted = pformat(self.all_configs)
        logger.info(f'All Configs: ${all_configs_formatted}')
