from back_end.dto.user_dto import UserDto
from back_end.utils.exceptions import MongoDbUserNotFoundException
from back_end.utils.settings_accumalator import Settings
from pymongo import MongoClient


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

    def get_user_by_phone_number(self, phone_number) -> UserDto:
        user = self.collection_users.find_one({'phone_number': phone_number})
        if user is None:
            raise MongoDbUserNotFoundException('User not found for the provided phone number.')
        return UserDto(**user)

    def update_user_name(self, user: UserDto, name: str):
        result = self.collection_users.update_one({'phone_number': user.phone_number}, {'$set': {'name': name}})
        if result.matched_count == 0:
            raise MongoDbUserNotFoundException('User not found for the provided phone number.')
        return result.modified_count

    def close_connection(self):
        self.client.close()
