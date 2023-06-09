from logging import getLogger
from pprint import pformat

from utils.utility_funcs import create_json, read_json

logger = getLogger('uvicorn')

app_configs_file = 'configs.json'
twilio_secrets_file = '/pigeon/secrets/twilio/.twilio-cli/config.json'
combined_configs_file = '/pigeon/secrets/.tmp_runtime_configs.json'


class ConfigLoader:
    def __init__(self, env: str):
        self.env = env
        self.combined_configs = self._combine_all_configs()
        self.configs = Configs(self.combined_configs)

    def _combine_all_configs(self):
        configs = {'configs': read_json(app_configs_file)[self.env]}
        twilio_secrets = {'twilio_secrets': read_json(twilio_secrets_file)}
        combined_configs = {**configs, **twilio_secrets}
        create_json(combined_configs_file, combined_configs)
        logger.info(f'All Configs: ${pformat(combined_configs)}')
        return combined_configs


class Configs:
    def __init__(self, combined_configs: dict):
        self.uvicorn = self.ConfigsUvicorn(combined_configs['configs']['uvicorn'])
        self.logging = self.ConfigsLogging(combined_configs['configs']['logging'])
        self.twilio = self.ConfigsTwilio(combined_configs['twilio_secrets'])

    class ConfigsUvicorn:
        def __init__(self, uvicorn_configs: dict):
            self.reload = uvicorn_configs['reload']

    class ConfigsLogging:
        def __init__(self, logging_configs: dict):
            self.level = logging_configs['level']

    class ConfigsTwilio:
        def __init__(self, twilio_configs: dict):
            self.sending_number = twilio_configs['twilio_sending_number']
            self.account_sid = twilio_configs['profiles']['pigeon']['accountSid']
            self.auth_token = twilio_configs['profiles']['pigeon']['authToken']
