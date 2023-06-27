from data_models.dao.mongodb_dao import MongodbDao
from data_models.dto.users_dto import UsersDto
from fastapi import FastAPI
from routes import LoggingCORSMiddleware, Routes
from send_sms import send_sms
from twilio.rest import Client
from utils.generic import custom_logger, logger
from utils.settings_accumalator import SettingsAccumalator


class Launcher:
    def __init__(self):
        self.settings = None
        self.launch()

    def configure_app(self, app: FastAPI):
        logger.info('Configuring FastAPI app..')
        app.add_middleware(
            LoggingCORSMiddleware,
            logger=logger
        )
        routes = Routes(self.settings)
        app.include_router(routes.router)

    def launch(self):
        logger.info('Accumalating all settings like configs and secrets..')
        self.settings = SettingsAccumalator().settings
        custom_logger.change_formatter(minimized=self.settings.configs_app.logging_format_minimized)
        custom_logger.change_logging_level(root_logging_level=self.settings.configs_app.logging_level)

        logger.info('Creating Twilio client..')
        twilio_client = Client(self.settings.secrets_twilio.account_sid, self.settings.secrets_twilio.auth_token)

        logger.info('Creating user DAO..')
        users_dao = MongodbDao(self.settings)

        logger.info('Temporary code..')
        # user1_dto: UsersDto = UsersDto("John Doe", "+19999999999")
        # inserted_id = users_dao.insert_user(user1_dto)
        # logger.info(f"User inserted in DB with ID: {inserted_id}")
        user1: UsersDto = users_dao.get_user_by_name('John Doe')
        logger.info(f'User retrieved from DB: {user1}')
        users_dao.close_connection()
        # send_sms(twilio_client, self.configs.twilio.sending_number, user1.phone_number)


app = FastAPI()
launcher = Launcher()
launcher.configure_app(app)
