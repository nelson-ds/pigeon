from data_models.dao.mongodb_dao import MongodbDao
from data_models.dto.users_dto import UsersDto
from utils.exceptions import MongoDbUserNotFoundException
from utils.generic import logger


class IncomingSms:
    def __init__(self, sms_from: str, sms_body: str, mongodb_dao: MongodbDao):
        self.sms_from = sms_from
        self.sms_body = sms_body
        self.mongodb_dao: MongodbDao = mongodb_dao
        self.user: UsersDto = self._get_user_from_db()

    def get_response(self) -> str:
        twiml_success_response = """
                    <Response>
                        <Message>Recieved SMS</Message>
                    </Response>
                """
        twiml_empty_response = '<Response/>'

        if self.user:
            response = twiml_success_response
        else:
            response = twiml_empty_response

        return response

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
            return user_dto
        except Exception as e:
            logger.error(f'Error while inserting new user in DB: {str(e)}')
            user_dto = None
        finally:
            return user_dto
