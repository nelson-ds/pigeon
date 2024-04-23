from datetime import datetime, timedelta
from typing import List, Optional

from backend.dto.user_dto import UserDto
from backend.utils.exceptions import MongoDbUserNotFoundException
from backend.utils.generic import logger
from backend.utils.settings_accumalator import Settings
from bson import ObjectId
from pymongo import MongoClient, errors


class MongodbDao:
    def __init__(self, settings: Settings):
        self.client = MongoClient(host=f'mongodb://{settings.configs_env.mongodb_container_name}',
                                  port=settings.configs_env.mongodb_port_number,
                                  username=settings.secrets_mongodb.username,
                                  password=settings.secrets_mongodb.password,
                                  authSource=settings.configs_env.mongodb_database_auth
                                  )
        self.db = self.client[f'{settings.configs_env.mongodb_database}']
        self.collection_users = self.db[settings.configs_app.mongodb_collection_users]

    def insert_user(self, user: UserDto) -> Optional[str]:
        """
        Inserts a user into the database if they do not already exist.
        :param user: UserDto containing user information.
        :return: The MongoDB ID of the inserted user or None if the user already exists.
        """
        inserted_id, user_dict = None, vars(user)
        user_dict.pop('_id', None)
        if self.collection_users.count_documents({'phone_number': user.phone_number}) == 0:
            try:
                result = self.collection_users.insert_one(user_dict)
                inserted_id = result.inserted_id
            except errors.PyMongoError as e:
                logger.error(f"Failed to insert user with phone number {user.phone_number}: {e}")
        else:
            logger.info(f"User with phone number {user.phone_number} already exists")
        return inserted_id

    def delete_user(self, user: UserDto) -> int:
        tomorrow = datetime.now() + timedelta(days=1)
        result = self.collection_users.update_one({'phone_number': user.phone_number}, {'$set': {'deletion_date': tomorrow}})
        if result.matched_count == 0:
            raise Exception('User not found or already deleted.')
        return result.matched_count

    def is_user_rate_limited(self, user: UserDto, rate_limit: int) -> bool:
        logger.info(f'Checking if user {user.phone_number} is rate limited..')
        user_rate_limited, now = False, datetime.now()
        day_after_tomorrow = now + timedelta(days=2)
        if user.deletion_date < day_after_tomorrow:
            logger.info(f'User {user.phone_number} recently off-boarded from the system..')
            user_rate_limited = True
        else:
            if user.time_last_sms is not None and now.date() > user.time_last_sms.date():
                self._update_sms_counter(user, 0)  # reset counter for user every new day
            else:
                if user.sms_counter <= rate_limit:
                    self._update_sms_counter(user, user.sms_counter + 1)
                else:
                    logger.info(f'User {user.phone_number} rate limit reached ({user.sms_counter} / {rate_limit})')
                    user_rate_limited = True
            self.update_time_last_sms(user, now)
        return user_rate_limited

    def _update_sms_counter(self, user: UserDto, sms_counter: int) -> int:
        result = self.collection_users.update_one({'phone_number': user.phone_number}, {'$set': {'sms_counter': sms_counter}})
        if result.matched_count == 0:
            raise MongoDbUserNotFoundException('User not found for the provided phone number.')
        return result.modified_count

    def get_user_by_phone_number(self, phone_number) -> UserDto:
        user = self.collection_users.find_one({'phone_number': phone_number})
        if user is None:
            raise MongoDbUserNotFoundException('User not found for the provided phone number.')
        return UserDto(**user)

    def update_time_last_sms(self, user: UserDto, time_last_sms: datetime) -> int:
        result = self.collection_users.update_one({'phone_number': user.phone_number}, {'$set': {'time_last_sms': time_last_sms}})
        if result.matched_count == 0:
            raise MongoDbUserNotFoundException('User not found for the provided phone number.')
        return result.modified_count

    def update_user_name(self, user: UserDto, name: str) -> int:
        result = self.collection_users.update_one({'phone_number': user.phone_number}, {'$set': {'name': name}})
        if result.matched_count == 0:
            raise MongoDbUserNotFoundException('User not found for the provided phone number.')
        return result.modified_count

    def update_user_cities(self, user: UserDto, cities: List[str]) -> int:
        result = self.collection_users.update_one({'phone_number': user.phone_number}, {'$set': {'cities_ca': cities}})
        if result.matched_count == 0:
            raise MongoDbUserNotFoundException('User not found for the provided phone number.')
        return result.modified_count

    def update_connection_details(self, user: UserDto, connected_phone_number: str, connected_name: str) -> int:
        result = self.collection_users.update_one({'phone_number': user.phone_number}, {'$set': {'connected_phone_number': connected_phone_number}})
        if result.matched_count == 0:
            raise MongoDbUserNotFoundException('User not found for the provided phone number.')
        else:
            self.collection_users.update_one({'phone_number': user.phone_number}, {'$set': {'connected_name': connected_name}})
        return result.modified_count

    def find_user_by_city(self, user: UserDto, city: str) -> UserDto:
        """
        Finds the first user who is familiar with given city and is not connected to any other user
        :param city: The city to search within the user data.
        :param exclude_user_id: The MongoDB ID of the user to be excluded from the search.
        :return: The first matching user document or None if no match is found.
        """
        connected_user = None
        try:
            query = {
                'cities_ca': {'$elemMatch': {'$regex': f'^\\s*{city}\\s*$', '$options': 'i'}},  # Regex to handle spaces & case-insensitivity
                'connected_phone_number': None,
                '_id': {'$ne': ObjectId(user._id)}  # Exclude current user's ID from the search
            }
            matched_user = self.collection_users.find_one(query)
            if matched_user is None:
                logger.info(f'Could not find any user to connect for {user.phone_number} and city {city}')
            else:
                connected_user = UserDto(**matched_user)
        except Exception as e:
            logger.error(f'Error finding user by city: {str(e)}')
        finally:
            return connected_user

    def close_connection(self):
        self.client.close()
