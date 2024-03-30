from typing import List

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
        self.is_user_name_known = self.user.name is not None
        self.are_user_cities_known = self.user.cities_ca is not None
        self.mongodb_langchain_dao: MongodbLangchainDao = MongodbLangchainDao(settings, sms_from)
        self.langchain_client = langchain_client

    def get_response(self) -> str:
        answer = None
        response = MessagingResponse()
        chat_history = self.mongodb_langchain_dao.chat_history
        if not self.is_user_onboarded:
            answer = self._get_new_user_onboarding_response()
            self.mongodb_langchain_dao.update_user_message(self.sms_body)
            self.mongodb_langchain_dao.update_ai_message(answer)
        else:
            llm_response = self.langchain_client.get_user_chat_response(chat_history, self.sms_from, self.sms_body)
            answer = llm_response
            if not self.is_user_name_known:
                answer = self._get_user_name_response(chat_history)
                self.mongodb_langchain_dao.delete_most_recent_messages(3)  # delete admin interactions from chat history
                self.mongodb_langchain_dao.update_ai_message(answer)
            elif not self.are_user_cities_known:
                answer = self._get_user_cities_response()
                self.mongodb_langchain_dao.delete_most_recent_messages(3)  # delete admin interactions from chat history
                self.mongodb_langchain_dao.update_ai_message(answer)
        response.message(answer)
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
        onboarding_response = \
            "Hello, welcome to PigeonMsg! I'm your assitant Pidge and I'll help you plan your next trip to any city in California!\n\n" + \
            "You can either ask your travel related questions to me (your helpful AI bird) or you can ask me to connect you to another " + \
            "human (more on that later).\n\n" + \
            "First, lets get familiar! " +  \
            "What should I call you? If you don't feel comfortable sharing your real name, reply with a made up one like \"Wanderer\" 😊 \n\n"
        return onboarding_response

    def _get_user_name_response(self, chat_history):
        logger.info(f'The name of the user is not yet stored - fetching it via langchain..')
        query = "What is my name? Respond by saying only my name and nothing else. If you don't know my name, say Unknown."
        user_name = self.langchain_client.get_admin_chat_response(chat_history, self.sms_from, query)
        self.mongodb_dao.update_user_name(self.user, user_name)
        user_name_response = \
            f"Hi {user_name}, nice to meet you! There are a couple long messages I'll send you as part of on-boarding to the platform - " +\
            "please bear with me.\n\nThis platform is sustained by folks who are willing to help others users (anonymously) " +\
            "by answering their questions about trip planning. " + \
            "A chat with another user will automatically expire in 24 hours but you can also " + \
            "end it any time you wish. If you are willing to assist other users, simply respond with the names of cities in California that" +\
            "you are familiar with (you can always change this later).\n\n" + \
            "For example, you can reply \"No\" if you don't want to help other users on this platform. If you are willing to help, " + \
            "reply with names of cities you are familiar with, like \"San Francisco, Mendocino...\""
        return user_name_response

    def _get_user_cities_response(self):
        chat_history = self.mongodb_langchain_dao.chat_history
        logger.info(f'The cities for the user are not yet stored - fetching it via langchain..')
        query = "What are the cities I have indicated I can help other users with? Respond by saying only comma seperated city names " +\
            "and nothing else. Make sure city names are not acronyms. If I have not given any city names, simply respond with Unknown."
        user_cities = self.langchain_client.get_admin_chat_response(chat_history, self.sms_from, query)
        user_cities_list = user_cities.strip().split(',')
        self.mongodb_dao.update_user_cities(self.user, user_cities_list)
        city_response = f"Great! I've noted that you're willing to help others with their travel plans to {user_cities}.\n\n"
        if len(user_cities_list) == 0:
            city_response = f"No worries, you can always let me know later if you change your mind.\n\n"
        user_cities_response = city_response + \
            "At any point, if you want to chat with a human about planing a trip to a city in California, reply with the command - " +\
            "\"pidge human <city name>\". If I know of another user who is famililar with that city, I'll connect you two " +\
            "anonymously! To get a list of all commands, reply with \"pidge commands\".\n\n" +\
            "You can of-course ask me questions anytime! " +\
            "Can I assist you with planning your next trip to any city in California?"

        return user_cities_response
