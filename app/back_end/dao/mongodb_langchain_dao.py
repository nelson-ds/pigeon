from back_end.utils.settings_accumalator import Settings
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory


class MongodbLangchainDao:
    def __init__(self, settings: Settings, user_phone_number):
        self.chat_history = MongoDBChatMessageHistory(
            session_id=user_phone_number,
            connection_string=f'mongodb://{settings.secrets_mongodb.username}:{settings.secrets_mongodb.password}@' +
            f'{settings.configs_env.mongodb_container_name}:{settings.configs_env.mongodb_port_number}/?authSource={settings.configs_env.mongodb_database_auth}',
            database_name=settings.configs_env.mongodb_database,
            collection_name=settings.configs_app.mongodb_collection_chats,
        )

    def update_user_message(self, query: str):
        self.chat_history.add_user_message(query)

    def update_ai_message(self, answer: str):
        self.chat_history.add_ai_message(answer)

    def delete_most_recent_messages(self, count: int):
        prev_messages = self.chat_history.collection.find().sort('_id', -1).limit(count)
        ids_to_delete = [message['_id'] for message in prev_messages]
        self.chat_history.collection.delete_many({'_id': {'$in': ids_to_delete}})
