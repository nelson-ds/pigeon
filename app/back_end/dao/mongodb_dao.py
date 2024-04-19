from datetime import datetime, timedelta
from typing import List

from back_end.dto.user_dto import UserDto
from back_end.utils.exceptions import MongoDbUserNotFoundException
from back_end.utils.generic import logger
from back_end.utils.settings_accumalator import Settings
from pymongo import MongoClient

SMS_ALLOWED_PER_DAY_PER_USER = 50
SMS_ALLOWED_PER_DAY_TOTAL = 1000


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

    def insert_user(self, user: UserDto):
        userDict = vars(user)
        del (userDict['_id'])
        result = self.collection_users.insert_one(userDict)
        return result.inserted_id

    def delete_user(self, user: UserDto) -> int:
        tomorrow = datetime.now() + timedelta(days=1)
        result = self.collection_users.update_one({'phone_number': user.phone_number}, {'$set': {'deletion_date': tomorrow}})
        if result.matched_count == 0:
            raise Exception('User not found or already deleted.')
        return result.matched_count

    def is_user_rate_limited(self, user: UserDto) -> bool:
        logger.info(f'Checking if user {user.phone_number} is rate limited')
        is_rate_limited = False
        now = datetime.now()
        day_after_tomorrow = now + timedelta(days=2)
        if user.deletion_date < day_after_tomorrow:
            logger.info(f'User {user.phone_number} recently off-boarded from the system..')
            is_rate_limited = True
        else:
            if user.time_last_sms is not None and now.date() > user.time_last_sms.date():
                self._update_sms_counter(user, 0)  # reset counter every new day
            else:
                if user.sms_counter <= SMS_ALLOWED_PER_DAY_PER_USER:
                    self._update_sms_counter(user, user.sms_counter + 1)
                else:
                    is_rate_limited = True
            self.update_time_last_sms(user, now)
        return is_rate_limited

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

    def close_connection(self):
        self.client.close()
