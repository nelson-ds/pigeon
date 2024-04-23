from typing import List

from backend.dao.mongodb_dao import MongodbDao
from backend.dao.mongodb_langchain_dao import (MongoDBChatMessageHistory,
                                               MongodbLangchainDao)
from backend.dto.user_dto import UserDto
from backend.langchain.llm_client import LangchainClient
from backend.twilio.outgoing_sms import send_sms
from backend.utils.exceptions import MongoDbUserNotFoundException
from backend.utils.generic import logger
from backend.utils.settings_accumalator import Settings
from twilio.rest import Client as TwilioClient
from twilio.twiml.messaging_response import MessagingResponse

SERVICE_NAME = 'Pigeon'
SERVICE_PHONE_NUMBER = '+00000000000'
SMS_ALLOWED_PER_DAY_FOR_SERVICE = 1000
SMS_ALLOWED_PER_DAY_PER_USER = 50


class IncomingSms:
    def __init__(self, settings: Settings, mongodb_dao: MongodbDao, twilio_client: TwilioClient, langchain_client: LangchainClient,
                 sms_from: str, sms_body: str):
        self.twilio_client = twilio_client
        self.sending_number = settings.secrets_twilio.sending_number
        self.sms_from = sms_from
        self.sms_body = sms_body[:1599]
        self.is_user_onboarded = True
        self.mongodb_dao: MongodbDao = mongodb_dao
        self.pigeon = self._get_user_from_db(SERVICE_PHONE_NUMBER, SERVICE_NAME)
        self.user: UserDto = self._get_user_from_db(self.sms_from)
        self.is_user_name_known = self.user.name is not None
        self.are_user_cities_known = self.user.cities_ca is not None
        self.mongodb_langchain_dao: MongodbLangchainDao = MongodbLangchainDao(settings, sms_from)
        self.langchain_client = langchain_client

    def get_response(self) -> str:
        message, response = '', MessagingResponse()
        is_service_rate_limited = self.mongodb_dao.is_user_rate_limited(self.pigeon, SMS_ALLOWED_PER_DAY_FOR_SERVICE)
        is_user_rate_limited = self.mongodb_dao.is_user_rate_limited(self.user, SMS_ALLOWED_PER_DAY_PER_USER)
        if not is_service_rate_limited and not is_user_rate_limited:
            chat_history = self.mongodb_langchain_dao.chat_history
            message = self._process_admin_commands(response, chat_history)
            if not message:
                if not self.user.connected_phone_number:
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
                    connected_user: UserDto = self.mongodb_dao.get_user_by_phone_number(self.user.connected_phone_number)
                    body = f'[{self.user.connected_name}]:\n\n {self.sms_body}'
                    is_sms_failed_response = self._send_sms_connected_user(connected_user, body)
                    if is_sms_failed_response:
                        message = is_sms_failed_response
            else:
                logger.warn(f'Detected admin command from user with phone number {self.sms_from} and processed it')
        else:
            logger.warn(f'Rate limit reached - not sending reply')
        message += self._get_message_trailer()
        response.message(message[:1599])
        return str(response)

    def _get_user_from_db(self, phone_number: str, name: str = None) -> UserDto:
        user = None
        try:
            user = self.mongodb_dao.get_user_by_phone_number(phone_number)
            logger.info(f'User with phone number {phone_number} fetched from DB')
        except MongoDbUserNotFoundException as e:
            logger.info(f'User does not exist in DB; adding the user to the DB..')
            user = self._add_new_user_to_db(phone_number, name)
        except Exception as e:
            logger.error(f'Error while fetching user from DB: {str(e)}')
        finally:
            return user

    def _add_new_user_to_db(self, phone_number: str, name: str = None) -> UserDto:
        user_dto = UserDto(phone_number=phone_number, name=name)
        try:
            inserted_id = self.mongodb_dao.insert_user(user_dto)
            logger.info(f'New user with phone number {phone_number} inserted in DB with ID: {inserted_id}')
            self.is_user_onboarded = False
            return user_dto
        except Exception as e:
            logger.error(f'Error while inserting new user in DB: {str(e)}')
            user_dto = None
        finally:
            return user_dto

    def _process_admin_commands(self, response: MessagingResponse, chat_history: MongoDBChatMessageHistory) -> bool:
        is_admin_command_invalid = False
        admin_command_response = ''
        sms_body_list = self.sms_body.lower().split(' ')
        try:
            if sms_body_list[0] == 'pidge':
                logger.info('Admin command invoked')
                command = sms_body_list[1]
                if command == 'help':
                    admin_command_response = self._handle_admin_command_help()
                elif command == 'name':
                    new_name = ' '.join(sms_body_list[2:])
                    if new_name:
                        admin_command_response = self._handle_admin_command_name(new_name, chat_history)
                    else:
                        is_admin_command_invalid = True
                elif command == 'cities':
                    new_cities = ' '.join(sms_body_list[2:])
                    if new_cities:
                        admin_command_response = self._handle_admin_command_cities(new_cities, chat_history)
                    else:
                        is_admin_command_invalid = True
                elif command == 'human':
                    city = ' '.join(sms_body_list[2:]).strip()
                    if city and city != 'Unknown':
                        admin_command_response = self._handle_admin_command_human(city)
                    else:
                        is_admin_command_invalid = True
                elif command == 'ai':
                    admin_command_response = self._handle_admin_command_ai()
                elif command == 'delete':
                    admin_command_response = self._handle_admin_command_delete()
                else:
                    is_admin_command_invalid = True
        except Exception as e:
            logger.error(f'Error while parsing admin command')
            admin_command_response = self._handle_admin_command_help(explicit=False)
        finally:
            if not admin_command_response and is_admin_command_invalid:
                logger.warn(f'Invalid admin command')
                admin_command_response = self._handle_admin_command_help(explicit=False)
            return admin_command_response

    def _handle_admin_command_help(self, explicit=True):
        help_response = ''
        if not explicit:
            help_response += 'I could not understand your command. Here is some help: \n'
        help_response += 'You have a limited number of messages per day using which you can chat with pidge ' + \
            f'({SMS_ALLOWED_PER_DAY_PER_USER - self.user.sms_counter} messages left for today). ' + \
            'If you want to invoke specific actions, you can use one of the following 6 commands:\n\n' + \
            '1. pidge help: gives the list of all commands.\n\n' + \
            '2. pidge name <name>: updates your name (example "pidge name Wanderer").\n\n' + \
            '3. pidge cities <cities>: deletes all previous cities and adds new list of cities you are willing to help other users with. ' + \
            'Example usage - "pidge cities San Francisco, Mendocino...".\n\n' + \
            '4. pidge human <city>: connects you to another human (if available) to help answer your travel questions for that city - ' + \
            'this connection expires after 24 hours. Please provide an accurate city name. Example usage "pidge human Sacramento".\n\n' + \
            'pidge ai: ends your ongoing connection with another human (if applicable) and connects you back to pidge!\n\n' + \
            'pidge delete: deletes all your information from the system and off-boards your from the platform.\n\n' + \
            'For more information, visit www.pigeonmsg.com'
        return help_response

    def _handle_admin_command_name(self, name: str, chat_history: MongoDBChatMessageHistory):
        logger.info(f'Updating user name..')
        query = 'I want to update my name in the system. Forget any name I might have told you earlier and call me only by my new name. ' + \
            f'My new name is {name}'
        _ = self.langchain_client.get_user_chat_response(chat_history, self.sms_from, query)
        user_name_response = self._get_user_name_response(update=True)
        return user_name_response

    def _handle_admin_command_cities(self, cities: str, chat_history: MongoDBChatMessageHistory):
        logger.info(f'Updating user cities..')
        query = 'I want to update the cities for which I am willing to help other users plan their travel. ' +\
            'If I told you any city names earlier related to this, forget them. ' + \
            'Only remember these new city names. ' + \
            f'The new city names are  {cities}'
        _ = self.langchain_client.get_user_chat_response(chat_history, self.sms_from, query)
        cities_response = self._get_user_cities_response(update=True)
        return cities_response

    def _handle_admin_command_human(self, city: str):
        logger.info(f'Searching human connections..')
        human_connection_response = 'You are already connected to another user.' +\
            'You must first end that connection by texting "pidge ai" before you request another connection.'
        if not self.user.connected_phone_number:
            human_connection_response = f'Unfortunately, no user in our system is familiar with the city - {city.title()} 😞. ' +\
                'Do try again in a few days as we are constantly on-boarding new users every day!'
            connected_user = self.mongodb_dao.find_user_by_city(self.user, city)
            logger.info(f'connected_user: ${connected_user}')
            if connected_user:
                connection_helper_name, connection_requestor_name = f'{city.upper()} HELPER', f'{city.upper()} HELP REQUESTOR'
                human_connection_response = f'Congratulations, we were able to find a user who is familiar with {city.title()} 🎉! ' + \
                    'I have connected you two and all future messages you send will be forwarded to this user.\n\n' + \
                    f'You will know you are chatting to this user by [{connection_helper_name}] prefixed before the message.\n\n' + \
                    'You (or the other user) may chose to end the connection any time by sending the text "pidge ai".'
                help_provider_response = f'Hello! Another user has requested some help with the city - {city.title()} ℹ️! ' + \
                    'I have connected you two and all future messages you send will be forwarded to this user.\n\n' + \
                    f'You will know you are chatting to this user by [{connection_requestor_name}] prefixed before the message.\n\n' + \
                    'You (or the other user) may chose to end the connection any time by sending the text "pidge ai".'
                self.mongodb_dao.update_connection_details(self.user, connected_user.phone_number, connection_requestor_name)
                self.mongodb_dao.update_connection_details(connected_user, self.user.phone_number, connection_helper_name)
                is_sms_failed_response = self._send_sms_connected_user(connected_user, help_provider_response)
                if is_sms_failed_response:
                    human_connection_response = is_sms_failed_response
        return human_connection_response

    def _handle_admin_command_ai(self):
        logger.info(f'Removing human connections..')
        connected_number = self.user.connected_phone_number
        ai_connection_response = 'If you were connected to another user on our service, that connection has now concluded.\n\n' +\
            'You\'re back to texting with your helpful AI, Pidge! 🪶'
        if connected_number:
            connected_user: UserDto = self.mongodb_dao.get_user_by_phone_number(connected_number)
            self.mongodb_dao.update_connection_details(self.user, None, None)
            self.mongodb_dao.update_connection_details(connected_user, None, None)
            self._send_sms_connected_user(connected_user, ai_connection_response)
        return ai_connection_response

    def _handle_admin_command_delete(self):
        self._handle_admin_command_ai()
        logger.info(f'Deleting all user data from the system..')
        self.mongodb_dao.delete_user(self.user)
        self.mongodb_langchain_dao.delete_chat_history()
        delete_response = 'All your data has been deleted from the system. If you want to join the platform again, ' + \
            'you will have to wait one day before you can be on-boarded.\n\nThanks for using PigeonMsg!'
        return delete_response

    def _send_sms_connected_user(self, connected_user: UserDto, body: str) -> str:
        response = ''
        is_service_rate_limited = self.mongodb_dao.is_user_rate_limited(self.pigeon, SMS_ALLOWED_PER_DAY_FOR_SERVICE)
        is_user_rate_limited = self.mongodb_dao.is_user_rate_limited(connected_user, SMS_ALLOWED_PER_DAY_PER_USER)
        if not is_service_rate_limited:
            if not is_user_rate_limited:
                is_message_sent = send_sms(self.twilio_client, self.sending_number, connected_user, body)
                if not is_message_sent:
                    response = 'Failed to send your previous SMS - try again after some time.'
            else:
                response = 'The user you are chatting with has reached their rate limit for the day - ' +\
                    'try chatting with them again after midnight, UTC.'
        else:
            logger.warn(f'{self.sms_from} has reached rate limit - not sending sms')
        return response

    def _get_message_trailer(self) -> str:
        trailer = ''
        sms_left_today = SMS_ALLOWED_PER_DAY_PER_USER - self.user.sms_counter
        if sms_left_today < 3 and sms_left_today >= 0:
            trailer += f'\n\nNOTE: You have {sms_left_today} sms left for today. This will reset to {SMS_ALLOWED_PER_DAY_PER_USER} sms at 12 am UTC'
        return trailer

    def _get_new_user_onboarding_response(self):
        logger.info(f'Triggering onboarding for new user..')
        onboarding_response = \
            'Hello, welcome to PigeonMsg! I\'m your assistant Pidge and I\'ll help you plan your next trip to any city in California!\n\n' + \
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
        if len(user_cities_list) == 0 or user_cities_list == ['Unknown']:
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
