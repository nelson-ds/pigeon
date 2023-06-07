from logging import getLogger
from pprint import pformat

from utils import create_json, read_json

logger = getLogger('uvicorn')

app_configs_file = 'configs.json'
twilio_secrets_file = '/pigeon/secrets/twilio/.twilio-cli/config.json'
combined_configs_file = '/pigeon/secrets/.tmp_runtime_configs.json'


class ConfigLoader:
    def __init__(self, env: str):
        self.env = env
        self.combined_configs = self._combine_all_configs()
        self.all_configs = self._prep_configs_for_runtime()
        self._print_configs()

    def _combine_all_configs(self):
        configs = read_json(app_configs_file)[self.env]
        twilio_secrets = read_json(twilio_secrets_file)
        combined_configs = {**configs, **twilio_secrets}
        return combined_configs

    def _prep_configs_for_runtime(self):
        create_json(combined_configs_file, self.combined_configs)
        return read_json(combined_configs_file)

    def _print_configs(self):
        all_configs_formatted = pformat(self.all_configs)
        logger.info(f'All Configs: ${all_configs_formatted}')
