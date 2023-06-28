from data_models.dao.mongodb_dao import MongodbDao
from fastapi import FastAPI
from twilio.rest import Client
from utils.generic import custom_logger, logger
from utils.settings_accumalator import SettingsAccumalator
from web_server.middleware import RouterLoggingMiddleware
from web_server.routes import Routes


class Launcher:
    def __init__(self):
        self.settings = None
        self.twilio_client = None
        self.mongodb_dao = None
        self.launch()

    def launch(self):
        logger.info('Accumalating all settings like configs and secrets..')
        self.settings = SettingsAccumalator().settings
        custom_logger.change_formatter(minimized=self.settings.configs_app.logging_format_minimized)
        custom_logger.change_logging_level(root_logging_level=self.settings.configs_app.logging_level)

        logger.info('Creating Twilio client..')
        self.twilio_client = Client(self.settings.secrets_twilio.account_sid, self.settings.secrets_twilio.auth_token)

        logger.info('Creating user DAO..')
        self.mongodb_dao = MongodbDao(self.settings)

    def configure_app(self, app: FastAPI):
        logger.info('Configuring FastAPI app..')
        app.add_middleware(
            RouterLoggingMiddleware,
            logger=logger
        )
        routes = Routes(self.settings, self.twilio_client, self.mongodb_dao)
        app.include_router(routes.router)


app = FastAPI()
launcher = Launcher()
launcher.configure_app(app)
