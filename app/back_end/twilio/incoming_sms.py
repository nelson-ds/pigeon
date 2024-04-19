from typing import List

from back_end.dao.mongodb_dao import SMS_ALLOWED_PER_DAY_PER_USER, MongodbDao
from back_end.dao.mongodb_langchain_dao import (MongoDBChatMessageHistory,
                                                MongodbLangchainDao)
from back_end.dto.user_dto import UserDto
from back_end.langchain.llm_client import LangchainClient
from back_end.utils.exceptions import MongoDbUserNotFoundException
from back_end.utils.generic import logger
from back_end.utils.settings_accumalator import Settings
from twilio.twiml.messaging_response import MessagingResponse


class IncomingSms:
    def __init__(self, settings: Settings, mongodb_dao: MongodbDao, langchain_client: LangchainClient, sms_from: str, sms_body: str):
        self.sms_from = sms_from
        self.sms_body = sms_body[:1600]
        self.is_user_onboarded = True
        self.mongodb_dao: MongodbDao = mongodb_dao
        self.user: UserDto = self._get_user_from_db()
        self.is_user_name_known = self.user.name is not None
        self.are_user_cities_known = self.user.cities_ca is not None
        self.mongodb_langchain_dao: MongodbLangchainDao = MongodbLangchainDao(settings, sms_from)
        self.langchain_client = langchain_client

    def get_response(self) -> str:
        message, response = '', MessagingResponse()
        is_user_rate_limited = self.mongodb_dao.is_user_rate_limited(self.user)
        if not is_user_rate_limited:
            chat_history = self.mongodb_langchain_dao.chat_history
            processed_potential_admin_command = self._process_admin_commands(response, chat_history)
            if not processed_potential_admin_command:
                message = None
                if not self.is_user_onboarded:
                    message = self._get_new_user_onboarding_response()
                    self.mongodb_langchain_dao.update_user_message(self.sms_body)
                    self.mongodb_langchain_dao.update_ai_message(message)
                else:
                    message = self.langchain_client.get_user_chat_response(chat_history, self.sms_from, self.sms_body)
                    if not self.is_user_name_known:
                        message = self._get_user_name_response()
                    elif not self.are_user_cities_known:
                        message = self._get_user_cities_response()
            else:
                logger.warn(f'Detected admin command from user with phone number {self.sms_from} and processed it')
        else:
            logger.warn(f'User with phone number {self.sms_from} has reached rate limit - not sending reply')
        response.message(message + self._get_message_trailer())
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
            logger.info(f'New user with phone number {self.sms_from} inserted in DB with ID: {inserted_id}')
            self.is_user_onboarded = False
            return user_dto
        except Exception as e:
            logger.error(f'Error while inserting new user in DB: {str(e)}')
            user_dto = None
        finally:
            return user_dto

    def _process_admin_commands(self, response: MessagingResponse, chat_history: MongoDBChatMessageHistory) -> bool:
        is_admin_command_parsed, is_admin_command_invalid = False, False
        sms_body_list = self.sms_body.split(' ')
        try:
            if sms_body_list[0] == 'pidge':
                is_admin_command_parsed = True
                logger.info('Admin command invoked')
                command = sms_body_list[1]
                if command == 'help':
                    self._handle_admin_command_help(response)
                elif command == 'name':
                    new_name = ' '.join(sms_body_list[2:])
                    if new_name:
                        self._handle_admin_command_name(response, new_name, chat_history)
                    else:
                        is_admin_command_invalid = True
                elif command == 'cities':
                    new_cities = ' '.join(sms_body_list[2:])
                    if new_cities:
                        self._handle_admin_command_cities(response, new_cities, chat_history)
                    else:
                        is_admin_command_invalid = True
                elif command == 'human':
                    pass
                elif command == 'ai':
                    pass
                elif command == 'delete':
                    self._handle_admin_command_delete(response)
                else:
                    is_admin_command_invalid = True
        except Exception as e:
            is_admin_command_parsed = True
            logger.error(f'Error while parsing admin command')
            self._handle_admin_command_help(response, explicit=False)
        finally:
            if is_admin_command_invalid:
                logger.warn(f'Invalid admin command')
                self._handle_admin_command_help(response, explicit=False)
            return is_admin_command_parsed

    def _handle_admin_command_help(self, response: MessagingResponse, explicit=True):
        message = ''
        logger.info(f'{message}')
        if not explicit:
            message += 'I could not understand your command. Here is some help: \n'
        message += 'You have a limited number of messages per day using which you can chat with pidge ' + \
            f'({SMS_ALLOWED_PER_DAY_PER_USER - self.user.sms_counter} messages left for today). ' + \
            'If at any time you want to invoke specific actions, you can use one of the following 6 commands:\n\n' + \
            'pidge help: gives the list of all commands\n\n' + \
            'pidge name <name>: updates your name (example "pidge name Wanderer")\n\n' + \
            'pidge cities <cities>: deletes all previous cities and adds new list of cities you are willing to help other users with ' + \
            '(example "pidge cities San Francisco, Mendocino...")\n\n' + \
            'pidge human <city>: connects you to another human (if available) to help answer your travel questions for that city - ' + \
            'this connection expires after 24 hours (example usage "pidge human Sacramento")\n\n' + \
            'pidge ai: ends your ongoing connection with another human (if applicable) and connects you back to pidge!\n\n' + \
            'pidge delete: deletes all your information from the system and off-boards your from the platform\n\n'
        response.message(message)

    def _handle_admin_command_name(self, response: MessagingResponse, name: str, chat_history: MongoDBChatMessageHistory):
        logger.info(f'Updating user name..')
        query = 'I want to update my name in the system. Forget any name I might have told you earlier and call me only by my new name. ' + \
            f'My new name is {name}'
        _ = self.langchain_client.get_user_chat_response(chat_history, self.sms_from, query)
        user_name_response = self._get_user_name_response(update=True)
        response.message(user_name_response)

    def _handle_admin_command_cities(self, response: MessagingResponse, cities: str, chat_history: MongoDBChatMessageHistory):
        logger.info(f'Updating user cities..')
        query = 'I want to update the cities for which I am willing to help other users plan their travel. ' +\
            'If I told you any city names earlier related to this, forget them. ' + \
            'Only remember these new city names. ' + \
            f'The new city names are  {cities}'
        _ = self.langchain_client.get_user_chat_response(chat_history, self.sms_from, query)
        cities_response = self._get_user_cities_response(update=True)
        response.message(cities_response)

    def _handle_admin_command_delete(self, response):
        logger.info(f'Deleting all user data from the system..')
        self.mongodb_dao.delete_user(self.user)
        self.mongodb_langchain_dao.delete_chat_history()
        message = 'All your data has been deleted from the system. If you want to join the platform again, ' + \
            'you will have to wait one day before you can be on-boarded again.\n\nThanks for using PigeonMsg!'
        response.message(message)

    def _get_message_trailer(self) -> str:
        trailer = ''
        sms_left_today = SMS_ALLOWED_PER_DAY_PER_USER - self.user.sms_counter
        if sms_left_today < 3 and sms_left_today >= 0:
            trailer += f'\n\nNOTE: You have {sms_left_today} sms left for today. This will reset to {SMS_ALLOWED_PER_DAY_PER_USER} sms at 12 am UTC'
        return trailer

    def _get_new_user_onboarding_response(self):
        logger.info(f'Triggering onboarding for new user..')
        onboarding_response = \
            'Hello, welcome to PigeonMsg! I\'m your assitant Pidge and I\'ll help you plan your next trip to any city in California!\n\n' + \
            'You can either ask your travel related questions to me (your helpful AI bird) or you can ask me to connect you to another ' + \
            'human (more on that later).\n\n' + \
            'First, lets get familiar! ' +  \
            'What should I call you? If you don\'t feel comfortable sharing your real name, reply with a made up one like "Wanderer" 😊 \n\n'
        return onboarding_response

    def _get_user_name_response(self, update=False):
        logger.info(f'Fetching username via langchain..')
        chat_history = self.mongodb_langchain_dao.chat_history
        query = 'What is my name? Respond by saying only my name and nothing else. If you don\'t know my name, say Unknown.'
        user_name = self.langchain_client.get_admin_chat_response(chat_history, self.sms_from, query)
        self.mongodb_dao.update_user_name(self.user, user_name)
        user_name_response = \
            f'Hi {user_name}, nice to meet you! There are a couple long messages I\'ll send you as part of on-boarding to the platform - ' +\
            'please bear with me.\n\nThis platform is sustained by folks who are willing to help other users ' +\
            'by answering their questions about trip planning (anonymously). ' + \
            'A chat with another user will automatically expire in 24 hours but you can also ' + \
            'end it any time you wish. If you are willing to assist other users, simply respond with the names of cities in California that' +\
            'you are familiar with (you can always change this later).\n\n' + \
            'For example, you can reply \"No\" if you don\'t want to help other users on this platform. If you are willing to help, ' + \
            'reply with names of cities you are familiar with, like "San Francisco, Mendocino..."'
        if update:
            user_name_response = \
                f'Got it, {user_name}! How can I assist you today with your travel plans to a city in California? ' + \
                'If you have any questions, feel free to ask!'
        self.mongodb_langchain_dao.delete_most_recent_messages(3)  # delete admin interactions from chat history
        self.mongodb_langchain_dao.update_ai_message(user_name_response)
        return user_name_response

    # FIXME: explore openai tool for getting structured output
    def _get_user_cities_response(self, update=False):
        logger.info(f'Fetching city names via langchain..')
        chat_history = self.mongodb_langchain_dao.chat_history
        query = 'What are the cities I have indicated I can help other users with? Respond by saying only comma seperated city names ' +\
            'and nothing else. Make sure city names are not acronyms. If I have not given any city names, simply respond with Unknown.'
        user_cities = self.langchain_client.get_admin_chat_response(chat_history, self.sms_from, query)
        user_cities_list = user_cities.strip().split(',')
        self.mongodb_dao.update_user_cities(self.user, user_cities_list)
        city_response = f'Great! I\'ve noted that you\'re willing to help others with their travel plans to {user_cities}.\n\n'
        if len(user_cities_list) == 0:
            city_response = f'No worries, you can always let me know later if you change your mind.\n\n'
        user_cities_response = city_response + \
            'At any point, if you want to chat with a human about planing a trip to a city in California, reply with the command - ' +\
            '"pidge human <city>". If I know of another user who is famililar with that city, I\'ll connect you two ' +\
            'anonymously! To get a list of all commands, reply with "pidge help".\n\n' +\
            'You can of-course ask me questions anytime! ' +\
            'Can I assist you with planning your next trip to any city in California?'
        self.mongodb_langchain_dao.delete_most_recent_messages(3)  # delete admin interactions from chat history
        self.mongodb_langchain_dao.update_ai_message(user_cities_response)
        return user_cities_response
