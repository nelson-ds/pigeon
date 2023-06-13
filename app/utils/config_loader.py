from logging import getLogger
from os import environ
from pprint import pformat

from dotenv import load_dotenv
from utils.utility_funcs import create_json, read_file, read_json

logger = getLogger('uvicorn')

env_path = '/pigeon/.env'
app_configs_file = '/pigeon/app/configs/configs.json'
twilio_secrets_file = '/pigeon/secrets/twilio/.twilio-cli/config.json'
db_username_file = '/pigeon/secrets/mongodb/mongodb_username.txt'
db_password_file = '/pigeon/secrets/mongodb/mongodb_password.txt'
combined_configs_file = '/pigeon/secrets/.tmp_runtime_configs.json'


class ConfigsEnv:
    def __init__(self):
        load_dotenv(env_path)
        self.environment = environ.get("ENVIRONMENT")
        self.db_container_name = environ.get("DB_CONTAINER_NAME")
        self.db_port = int(environ.get("DB_PORT"))
        self.db_name = environ.get("DB_NAME")


class ConfigLoader:
    def __init__(self):
        self.configs_env = ConfigsEnv()
        self.combined_configs = self._combine_all_configs(self.configs_env)
        self.configs = Configs(self.configs_env, self.combined_configs)

    def _combine_all_configs(self, configs_env: ConfigsEnv):
        env = {'env': vars(configs_env)}
        configs = {'configs': read_json(app_configs_file)[configs_env.environment]}
        mongodb_secrets = {'mongodb_secrets': {'username': read_file(db_username_file), 'password': read_file(db_password_file)}}
        twilio_secrets = {'twilio_secrets': read_json(twilio_secrets_file)}

        combined_configs = {**env, **configs, **mongodb_secrets, **twilio_secrets}
        create_json(combined_configs_file, combined_configs)
        logger.info(f'All Configs: ${pformat(combined_configs)}')
        return combined_configs


class Configs:
    def __init__(self, configs_env: ConfigsEnv, combined_configs: dict):
        self.env = configs_env
        self.uvicorn = self.ConfigsUvicorn(combined_configs['configs']['uvicorn'])
        self.logging = self.ConfigsLogging(combined_configs['configs']['logging'])
        self.mongodb = self.ConfigsMongodb(combined_configs['mongodb_secrets'], combined_configs['configs']['mongodb'])
        self.twilio = self.ConfigsTwilio(combined_configs['twilio_secrets'])

    class ConfigsUvicorn:
        def __init__(self, uvicorn_configs: dict):
            self.port = uvicorn_configs['port']
            self.reload = uvicorn_configs['reload']

    class ConfigsLogging:
        def __init__(self, logging_configs: dict):
            self.level = logging_configs['level']

    class ConfigsMongodb:
        def __init__(self, db_secrets: dict, db_configs: dict):
            self.username = db_secrets['username']
            self.password = db_secrets['password']
            self.collection_users = db_configs['collection_users']

    class ConfigsTwilio:
        def __init__(self, twilio_configs: dict):
            self.sending_number = twilio_configs['twilio_sending_number']
            self.account_sid = twilio_configs['profiles']['pigeon']['accountSid']
            self.auth_token = twilio_configs['profiles']['pigeon']['authToken']
