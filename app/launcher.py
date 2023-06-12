from logging import getLevelName, getLogger

from data_models.dao.user_dao import UserDAO
from data_models.dto.user_dto import UserDTO
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
        user_dao = UserDAO(self.configs)

        # self.logger.info('Temporary code..')
        # user_dto = UserDTO("John Doe", "+19999999999")
        # inserted_id = user_dao.insert_user(user_dto)
        # self.logger.info(f"User inserted in DB with ID: {inserted_id}")
        # user = user_dao.get_user_by_id(inserted_id)
        # self.logger.info(f"User retrieved from DB: {user}")
        # user_dao.close_connection()

        # send_sms(twilio_client, self.configs.twilio.sending_number, user.phone_number)


app = FastAPI()
launcher = Launcher()
launcher.configure_app(app)
