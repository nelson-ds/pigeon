from langchain.agents import (AgentType, create_csv_agent, initialize_agent,
                              load_tools)
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI, Replicate
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schemas import AIMessage, HumanMessage, SystemMessage

llm = OpenAI()
llm2 = Replicate(model='replicate/llama-2-70b-chat:<apicode>')
print(llm)
response = llm("What is a framework")
print(response)


chat = ChatOpenAI()
messages = [
    SystemMessage(content='''
                You are a very passionate nerdy videogame master. you know how to defeat all games on Nintendo
                You are helpful, you always use the geekiest slang for kids that you can."
    '''),
    HumanMessage(content="What is the latest release of the Zelda franchise")
]
tools = load_tools(["serpapi"], llm=chat)
agent = initialize_agent(tools, chat, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
# response = chat(messages=message)
response = agent.run(ChatPromptTemplate.from_messages(messages).format())
print(response)


llm3 = OpenAI(temperature=0)
parser = CommaSeparatedListOutputParser()
recipe_prompt = PromptTemplate('''
 From the video game Breath of the wild, list the ingredients for the {dish}
 {format_instructions}
 ''',
                               input_variable=['dish'],
                               partial_variables={'format_instructions': parser.get_format_instructions}

                               )
# partial_variables=parser.get_format_instructions()
# response = llm(recipe_promt.format(dish='crab risotto'))
# print(response)
query = recipe_prompt.format(dish='crab_risotto')
print(query)
response = llm3(query)
ingredients = parser.parse(response)


llm4 = OpenAI()
agent = create_csv_agent(
    llm4,
    'shrines.csv',
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
response = agent.run('Count how many shrines are there in each area?')
print(response)


response = chain.run("I cannot find the frickin shrine")
# test streamlit for local chat agent
