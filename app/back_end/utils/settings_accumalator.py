from os import environ

from back_end.utils.generic import create_json, file_to_dict, logger, read_json
from dotenv import load_dotenv

env_configs_file = '/pigeon/.env'
app_configs_file = '/pigeon/app/configs/configs.json'
app_secrets_file = '/pigeon/secrets/app.json'
twilio_secrets_file = '/pigeon/secrets/twilio/.twilio-cli/config.json'
db_secrets_file = '/pigeon/secrets/mongodb/mongodb_credentials.txt'
combined_configs_file = '/pigeon/secrets/tmp_runtime_configs.json'


class ConfigsEnv:
    def __init__(self):
        load_dotenv(env_configs_file)
        self.environment = environ.get('ENVIRONMENT')
        self.app_port_number = int(environ.get('APP_PORT_NUMBER'))
        self.mongodb_database = environ.get('MONGO_INITDB_DATABASE')
        self.mongodb_database_auth = environ.get('MONGO_AUTH_DATABASE')
        self.mongodb_port_number = int(environ.get('MONGODB_PORT_NUMBER'))
        self.mongodb_container_name = environ.get('MONGODB_CONTAINER_NAME')


class SettingsAccumalator:
    def __init__(self):
        self.configs_env = ConfigsEnv()
        self.combined_configs = self._combine_all_configs(self.configs_env)
        self.settings = Settings(self.configs_env, self.combined_configs)

    def _combine_all_configs(self, configs_env: ConfigsEnv):
        env = {'env': vars(configs_env)}
        configs_json = read_json(app_configs_file)
        configs_common = configs_json['common']
        configs_env = configs_json[configs_env.environment]
        configs = {'configs': {**configs_common, **configs_env}}
        app_secrets = {'secrets_app': read_json(app_secrets_file)}
        mongodb_secrets = {'secrets_mongodb': file_to_dict(db_secrets_file, '=')}
        twilio_secrets = {'secrets_twilio': read_json(twilio_secrets_file)}
        combined_configs = {**env, **configs, **app_secrets, **mongodb_secrets, **twilio_secrets}
        create_json(combined_configs_file, combined_configs)
        logger.info(f'All Configs: {combined_configs}')
        return combined_configs


class Settings:
    def __init__(self, configs_env: ConfigsEnv, combined_configs: dict):
        self.configs_env = configs_env
        self.configs_app = self.ConfigsApp(combined_configs['configs'])
        self.secrets_app = self.SecretsApp(combined_configs['secrets_app'])
        self.secrets_mongodb = self.SecretsMongodb(combined_configs['secrets_mongodb'])
        self.secrets_twilio = self.SecretsTwilio(combined_configs['secrets_twilio'])

    class ConfigsApp:
        def __init__(self, app_configs: dict):
            self.uvicorn_reload = app_configs['uvicorn_reload']
            self.logging_format_minimized = bool(app_configs['logging_format_minimized'])
            self.logging_level = app_configs['logging_level']
            self.mongodb_collection_users = app_configs['mongodb_collection_users']
            self.web_route_home = app_configs['web_route_home']
            self.web_route_sms = app_configs['web_route_sms']
            self.web_route_static = app_configs['web_route_static']
            self.web_static_dir = app_configs['web_static_dir']
            self.web_templates_dir = app_configs['web_templates_dir']
            self.web_template_home_file_name = app_configs['web_template_home_file_name']

    class SecretsApp:
        def __init__(self, app_secrets: dict):
            self.app_username = app_secrets['app_username']
            self.app_password = app_secrets['app_password']

    class SecretsMongodb:
        def __init__(self, db_secrets: dict):
            self.username = db_secrets['MONGO_INITDB_ROOT_USERNAME']
            self.password = db_secrets['MONGO_INITDB_ROOT_PASSWORD']

    class SecretsTwilio:
        def __init__(self, twilio_secrets: dict):
            self.sending_number = twilio_secrets['twilio_sending_number']
            self.account_sid = twilio_secrets['profiles']['pigeon']['accountSid']
            self.auth_token = twilio_secrets['profiles']['pigeon']['authToken']
