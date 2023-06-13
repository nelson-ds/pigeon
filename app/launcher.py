from logging import getLevelName, getLogger

from data_models.dao.mongodb_dao import MongodbDao
from data_models.dto.users_dto import UsersDto
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from send_sms import send_sms
from twilio.rest import Client
from utils.config_loader import ConfigLoader
from utils.utility_funcs import configure_logger


class Launcher:
    def __init__(self):
        self.logger = getLogger("uvicorn")
        configure_logger(self.logger)
        self.configs = None

        self.launch()

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

    def launch(self):
        self.logger.info(f'Setting up config..')
        self.configs = ConfigLoader().configs
        self.logger.setLevel(getLevelName(self.configs.logging.level))

        self.logger.info('Creating Twilio client..')
        twilio_client = Client(self.configs.twilio.account_sid, self.configs.twilio.auth_token)

        self.logger.info('Creating user DAO..')
        users_dao = MongodbDao(self.configs)

        self.logger.info('Temporary code..')
        # user1_dto: UsersDto = UsersDto("John Doe", "+19999999999")
        # inserted_id = users_dao.insert_user(user1_dto)
        # self.logger.info(f"User inserted in DB with ID: {inserted_id}")
        user1: UsersDto = users_dao.get_user_by_name('John Doe')
        self.logger.info(f"User retrieved from DB: {user1}")
        users_dao.close_connection()
        # send_sms(twilio_client, self.configs.twilio.sending_number, user.phone_number)


app = FastAPI()
launcher = Launcher()
launcher.configure_app(app)
