from back_end.dao.mongodb_dao import MongodbDao
from back_end.dto.users_dto import UsersDto
from back_end.utils.exceptions import MongoDbUserNotFoundException
from back_end.utils.generic import logger
from twilio.twiml.messaging_response import MessagingResponse


class IncomingSms:
    def __init__(self, sms_from: str, sms_body: str, mongodb_dao: MongodbDao):
        self.sms_from = sms_from
        self.sms_body = sms_body
        self.is_user_onboarded = True
        self.mongodb_dao: MongodbDao = mongodb_dao
        self.user: UsersDto = self._get_user_from_db()

    def get_response(self) -> str:
        response = MessagingResponse()

        if not self.is_user_onboarded:
            new_user_onboarding_response = self._get_new_user_onboarding_response()
            response.message(new_user_onboarding_response)
        else:
            response.message('Recieved your sms')

        return str(response)

    def _get_user_from_db(self) -> UsersDto:
        user = None
        try:
            user = self.mongodb_dao.get_user_by_phone_number(self.sms_from)
            logger.info(f'User with phone number {self.sms_from} fetched from DB')
        except MongoDbUserNotFoundException as e:
            logger.info(f'User does not exist in DB; adding the user to the DB..')
            user = self._add_new_user_to_db()
        except Exception as e:
            logger.error(f'Error while fetching user from DB: {str(e)}')
        finally:
            return user

    def _add_new_user_to_db(self) -> UsersDto:
        user_dto = UsersDto('', self.sms_from)
        try:
            inserted_id = self.mongodb_dao.insert_user(user_dto)
            logger.info(f"New user with phone number {self.sms_from} inserted in DB with ID: {inserted_id}")
            self.is_user_onboarded = False
            return user_dto
        except Exception as e:
            logger.error(f'Error while inserting new user in DB: {str(e)}')
            user_dto = None
        finally:
            return user_dto

    def _get_new_user_onboarding_response(self):
        logger.info(f'Triggering onboarding for new user..')
        twiml_new_user_name_request = \
            "Hello, welcome to PigeonMsg! I'm your assitant Pidge and I'll help you plan your next trip in California." + \
            "Before we get started, what should I call you? If you don't feel comfortable sharing your real name, use a made up one like 'Wanderer' :-)" + \
            "If you want to change what I call you in the future, just text 'pidge new-name <new name here>"

        return twiml_new_user_name_request
