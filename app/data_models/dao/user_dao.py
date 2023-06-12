from pymongo import MongoClient
from utils.config_loader import Configs


class UserDAO:
    def __init__(self, configs: Configs):

        self.client = MongoClient(f'mongodb://localhost:{configs.env.db_port}/')
        self.db = self.client[f'{configs.env.db_name}']
        self.collection = self.db['users']

    def insert_user(self, user):
        document = {
            "name": user.name,
            "phone_number": user.phone_number
        }
        result = self.collection.insert_one(document)
        return result.inserted_id

    def get_user_by_phone_number(self, phone_number):
        user = self.collection.find_one({"phone_number": phone_number})
        return user

    def close_connection(self):
        self.client.close()
