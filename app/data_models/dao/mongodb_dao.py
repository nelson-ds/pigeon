from data_models.dto.users_dto import UsersDto
from pymongo import MongoClient
from utils.exceptions import MongoDbUserNotFoundException
from utils.settings_accumalator import Settings


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

    def insert_user(self, user: UsersDto):
        userDict = vars(user)
        del (userDict['_id'])
        result = self.collection_users.insert_one(userDict)
        return result.inserted_id

    def get_user_by_phone_number(self, phone_number) -> UsersDto:
        user = self.collection_users.find_one({"phone_number": phone_number})
        if user is None:
            raise MongoDbUserNotFoundException
        return UsersDto(**user)

    def get_user_by_name(self, name) -> UsersDto:
        user = self.collection_users.find_one({"name": name})
        return UsersDto(**user)

    def close_connection(self):
        self.client.close()
