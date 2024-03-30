from back_end.dao.mongodb_dao import MongodbDao
from back_end.dao.mongodb_langchain_dao import MongodbLangchainDao
from back_end.dto.user_dto import UserDto
from back_end.langchain.llm_client import LangchainClient
from back_end.utils.exceptions import MongoDbUserNotFoundException
from back_end.utils.generic import logger
from back_end.utils.settings_accumalator import Settings
from twilio.twiml.messaging_response import MessagingResponse


class IncomingSms:
    def __init__(self, settings: Settings, mongodb_dao: MongodbDao, langchain_client: LangchainClient, sms_from: str, sms_body: str):
        self.pigeon_invocation = {'pigeon', 'pidge', 'pgn'}
        self.sms_from = sms_from
        self.sms_body = sms_body
        self.is_user_onboarded = True
        self.mongodb_dao: MongodbDao = mongodb_dao
        self.user: UserDto = self._get_user_from_db()
        self.mongodb_langchain_dao: MongodbLangchainDao = MongodbLangchainDao(settings, sms_from)
        self.langchain_client = langchain_client

    def get_response(self) -> str:
        answer = None
        response = MessagingResponse()
        if not self.is_user_onboarded:
            answer = self._get_new_user_onboarding_response()
        else:
            body_list = self.sms_body.split(' ')
            if body_list[0] in self.pigeon_invocation:
                logger.info(f'Admin command invoked by the user')
                answer = self._get_admin_command_responses()
            else:
                chat_history = self.mongodb_langchain_dao.chat_history
                if len(chat_history.messages) == 2:
                    logger.info(f'Second message sent by user - assuming first word is the name')  # FIXME: parse this from llm response
                    self.mongodb_dao.update_user_name(self.user, body_list[0])
                llm_response = self.langchain_client.get_chat_response(chat_history, self.sms_from, self.sms_body)
                answer = llm_response
        response.message(answer)
        logger.info(f'query: {self.sms_body}; langchain_answer: {answer}')
        self.mongodb_langchain_dao.update_chat_history(self.sms_body, answer)
        return str(response)

    def _get_user_from_db(self) -> UserDto:
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

    def _add_new_user_to_db(self) -> UserDto:
        user_dto = UserDto(phone_number=self.sms_from)
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
        twiml_new_user_name_response = \
            "Hello, welcome to PigeonMsg! I'm your assitant Pidge and I'll help you plan your next trip to a city in California!\n\n" + \
            "Before we get started, what should I call you? If you don't feel comfortable sharing your real name, use a made up one like 'Wanderer' 😊 \n\n" + \
            "If you want to change what I call you in the future, just text 'pidge new-name <new name here>"
        return twiml_new_user_name_response

    def _get_admin_command_responses(self):  # FIXME: implement this
        twiml_admin_command_response = 'Unrecognized admin command sent to Pidge'
        return twiml_admin_command_response
