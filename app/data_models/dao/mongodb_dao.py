from data_models.dto.users_dto import UsersDto
from pymongo import MongoClient
from utils.exceptions import MongoDbUserNotFoundException
from utils.settings_accumalator import Settings


class MongodbDao:
    def __init__(self, configs: Settings):

        self.client = MongoClient(host=f'mongodb://{configs.configs_env.mongodb_container_name}',
                                  port=configs.configs_env.mongodb_port_number,
                                  username=configs.secrets_mongodb.username,
                                  password=configs.secrets_mongodb.password,
                                  authSource=configs.configs_env.mongodb_database_auth
                                  )
        self.db = self.client[f'{configs.configs_env.mongodb_database}']
        self.collection_users = self.db[configs.configs_mongodb.collection_users]

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
