from logging import getLogger

from data_models.dto.users_dto import UsersDto
from pymongo import MongoClient
from utils.config_loader import Configs

logger = getLogger('uvicorn')


class MongodbDao:
    def __init__(self, configs: Configs):

        self.client = MongoClient(host=f'mongodb://{configs.env.mongodb_container_name}',
                                  port=configs.env.mongodb_port_number,
                                  username=configs.mongodb.username,
                                  password=configs.mongodb.password,
                                  authSource=configs.env.mongodb_database_auth
                                  )
        self.db = self.client[f'{configs.env.mongodb_database}']
        self.collection_users = self.db[configs.mongodb.collection_users]

    def insert_user(self, user: UsersDto):
        userDict = vars(user)
        del (userDict['_id'])
        result = self.collection_users.insert_one(userDict)
        return result.inserted_id

    def get_user_by_phone_number(self, phone_number) -> UsersDto:
        user = self.collection_users.find_one({"phone_number": phone_number})
        return UsersDto(**user)

    def get_user_by_name(self, name) -> UsersDto:
        user = self.collection_users.find_one({"name": name})
        return UsersDto(**user)

    def close_connection(self):
        self.client.close()
