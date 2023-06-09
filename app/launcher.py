from logging import getLevelName, getLogger
from os import environ

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from twilio.rest import Client
from utils.config_loader import ConfigLoader
from utils.utility_funcs import configure_logger

env_path = '/pigeon/.env'


class Launcher:
    def __init__(self):
        load_dotenv(env_path)
        self.env = environ.get("ENVIRONMENT")

        self.logger = getLogger("uvicorn")
        configure_logger(self.logger)

        self.configs = None
        self.twilio_client = None

        self.launch()

    def launch(self):
        self.logger.info(f'Setting up config for {self.env} environment..')
        self.configs = ConfigLoader(self.env).configs
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