from backend.dao.mongodb_dao import MongodbDao
from backend.langchain.llm_client import LangchainClient
from backend.middleware import RouterLoggingMiddleware
from backend.routes import Routes
from backend.utils.generic import custom_logger, logger
from backend.utils.settings_accumalator import SettingsAccumalator
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from twilio.rest import Client as TwilioClient


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

        logger.info('Creating user DAO..')
        self.mongodb_dao = MongodbDao(self.settings)

        logger.info('Creating Twilio client..')
        self.twilio_client = TwilioClient(self.settings.secrets_twilio.account_sid, self.settings.secrets_twilio.auth_token)

        logger.info('Creating LangChain client..')
        self.langchain_client = LangchainClient(self.settings)

    def configure_app(self, app: FastAPI):
        logger.info('Configuring FastAPI app..')
        app.add_middleware(
            RouterLoggingMiddleware,
            logger=logger
        )
        routes = Routes(self.settings, self.mongodb_dao, self.twilio_client, self.langchain_client)
        app.include_router(routes.router)
        app.mount(
            path=self.settings.configs_app.web_route_static,
            app=StaticFiles(directory=self.settings.configs_app.web_static_dir),
            name="static"
        )


app = FastAPI()
launcher = Launcher()
launcher.configure_app(app)
