from logging import getLevelName, getLogger
from os import environ

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from twilio.rest import Client
from utils.config_loader import ConfigLoader
from utils.utility_funcs import configure_logger

env_path = '/pigeon/.env'


class Launcher:
    def __init__(self):
        self.logger = getLogger("uvicorn")
        configure_logger(self.logger)
        self.configs = None
        self.twilio_client = None

        load_dotenv(env_path)
        self.launch(environ.get("ENVIRONMENT"))

    def launch(self, env):
        self.logger.info(f'Setting up config for {env} environment..')
        self.configs = ConfigLoader(env).configs
        self.logger.setLevel(getLevelName(self.configs.logging.level))

        self.logger.info('Creating Twilio client..')
        self.twilio_client = Client(self.configs.twilio.account_sid, self.configs.twilio.auth_token)

    def configure_app(self, app):
        self.logger.info('Configuring FastAPI app..')
        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
        app.include_router(router)


app = FastAPI()
launcher = Launcher()
launcher.configure_app(app)
