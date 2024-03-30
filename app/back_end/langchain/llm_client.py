import sys
from typing import Dict

from back_end.utils.generic import logger
from back_end.utils.settings_accumalator import Settings
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_core.messages.ai import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

__import__('pysqlite3')


class LangchainClient:

    def __init__(self, settings: Settings):
        self.settings = settings
        self.chat = self._init_llm_chat()
        self.retriever = self._init_retriever()
        self.prompt_get_updated_user_question = self._create_prompt_get_updated_user_question()
        self.prompt_answer_user_question = self._create_prompt_answer_user_question()
        self.prompt_admin = self._create_prompt_admin()

    def _init_llm_chat(self):
        logger.info('Initializing OpenAI chat..')
        chat = ChatOpenAI(
            openai_api_key=self.settings.secrets_openai.api_key,
            model=self.settings.configs_app.openai_model,
            temperature=self.settings.configs_app.openai_temperature
        )
        return chat

    def _init_retriever(self):
        logger.info('Initializing retriever for RAG..')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')  # https://docs.trychroma.com/troubleshooting#sqlite
        loader = DirectoryLoader(f'{self.settings.configs_app.langchain_retrieval_docs_dir}')
        data = loader.load()
        logger.info(f'Loaded {len(data)} retrieval documents for LangChain')
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
        all_splits = text_splitter.split_documents(data)
        vectorstore = Chroma.from_documents(documents=all_splits, embedding=OpenAIEmbeddings(openai_api_key=self.settings.secrets_openai.api_key))
        retriever = vectorstore.as_retriever(k=4)  # k is the number of chunks to retrieve
        return retriever

    def _create_prompt_get_updated_user_question(self):
        logger.info('Creating prompt to update user question based on chat history..')
        standalone_system_prompt = """
        Given a chat history and a follow-up question, rephrase the follow-up question to be a standalone question. \
        Do NOT answer the question, just reformulate it if needed, otherwise return it as is. \
        Only return the final standalone question. \
        """
        return ChatPromptTemplate.from_messages(
            [
                ("system", standalone_system_prompt),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )

    def _create_prompt_answer_user_question(self):
        logger.info('Creating prompt to answer user question based on chat history & context..')
        return ChatPromptTemplate.from_messages(
            [
                ("system",
                 "You are a text message bot called pidge. You will help you plan their next trip to any city in California." +
                 "Always be concise in your answers. Always reply in 50 words or less. Only answer questions related to travel and nothing else." +
                 "You will first try to answer the user's questions based on the below context:\n\n{context}"),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )

    def _create_prompt_admin(self):
        logger.info('Creating admin prompt to fetch the name of the user')
        return ChatPromptTemplate.from_messages(
            [
                ("system", "Answer the question based on the chat history."),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )

    def _parse_retriever_input(self, params: Dict):
        return params["question"]

    """
    This method tries to answer the user question via following steps:
        1. passes user question, chat history & prompt to chat agent which will generate an updated user question
        2. passes updated user question to a vector store containing ALL docs to fetch only relevant (similar) docs (forming context for question)
        3. passes context (retrieved doc chunks), user question, chat history & prompt to chat agent which will generate answer
    """

    def get_user_chat_response(self, chat_history: MongoDBChatMessageHistory, phone_number: str, query: str) -> AIMessage:

        # binds the doc retrieval prompt for retrieving relevant docs to a chat agent
        chain_updated_user_question = self.prompt_get_updated_user_question | self.chat | StrOutputParser()

        # generates context by passing doc retrieval prompt & all docs to chat agent to fetch only relevant docs (based on question & chat history)
        chain_doc_retriever = RunnablePassthrough.assign(context=chain_updated_user_question | self.retriever |
                                                         (lambda docs: "\n\n".join([d.page_content for d in docs])))

        # binds the retrieved relevant docs (context) & the user q&a prompt to a chat agent
        chain_rag = (chain_doc_retriever | self.prompt_answer_user_question | self.chat | StrOutputParser())

        chain_rag_with_history = RunnableWithMessageHistory(
            chain_rag,
            lambda session_id: chat_history,
            input_messages_key="question",
            history_messages_key="history",
        )

        config = {"configurable": {"session_id": phone_number}}
        response = chain_rag_with_history.invoke({"question": query}, config=config)
        logger.info(f'query: {query}; langchain_answer: {response}')
        return response

    def get_admin_chat_response(self, chat_history: MongoDBChatMessageHistory, phone_number: str, query: str):
        chain_admin_chat = self.prompt_admin | self.chat | StrOutputParser()
        chain_chat_with_history = RunnableWithMessageHistory(
            chain_admin_chat,
            lambda session_id: chat_history,
            input_messages_key="question",
            history_messages_key="history"
        )
        config = {"configurable": {"session_id": phone_number}}
        response = chain_chat_with_history.invoke({"question": query}, config=config)
        logger.info(f'query: {query}; langchain_answer: {response}')
        return response
