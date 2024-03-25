import sys
from typing import Dict

from back_end.utils.generic import logger
from back_end.utils.settings_accumalator import Settings
from langchain.chains.combine_documents import create_stuff_documents_chain
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
        self.doc_retriever_prompt = self._create_doc_retriever_prompt()
        self.user_qa_prompt = self._create_user_qa_prompt()

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

    def _create_doc_retriever_prompt(self):
        logger.info('Creating doc retriever prompt..')
        standalone_system_prompt = """
        Given a chat history and a follow-up question, rephrase the follow-up question to be a standalone question. \
        Do NOT answer the question, just reformulate it if needed, otherwise return it as is. \
        Only return the final standalone question. \
        """
        doc_retriever_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", standalone_system_prompt),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )
        return doc_retriever_prompt

    def _create_user_qa_prompt(self):
        logger.info('Creating user QA prompt..')
        user_qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.settings.configs_app.chat_prompt +
                 "You will first try to answer the user's questions based on the below context:\n\n{context}"),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )
        return user_qa_prompt

    def _parse_retriever_input(self, params: Dict):
        return params["question"]

    def get_chat_response(self, chat_history: MongoDBChatMessageHistory, phone_number: str, query: str) -> AIMessage:

        doc_question_chain = self.doc_retriever_prompt | self.chat | StrOutputParser()

        retriever_chain = RunnablePassthrough.assign(context=doc_question_chain | self.retriever |
                                                     (lambda docs: "\n\n".join([d.page_content for d in docs])))

        rag_chain = (retriever_chain | self.user_qa_prompt | self.chat | StrOutputParser())

        # chain = self.user_qa_prompt | self.chat
        retrieval_chain_with_history = RunnableWithMessageHistory(
            rag_chain,
            lambda session_id: chat_history,
            input_messages_key="question",
            history_messages_key="history",
        )

        config = {"configurable": {"session_id": phone_number}}
        # response = retrieval_chain_with_history.invoke(
        #     {"question": query, "context": self._parse_retriever_input | self.retriever}, config=config)
        response = retrieval_chain_with_history.invoke({"question": query}, config=config)
        return response
