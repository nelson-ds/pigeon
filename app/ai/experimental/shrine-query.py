from langchain.agents import AgentType, create_csv_agent
from langchain.llms import OpenAI

llm = OpenAI()

agent = create_csv_agent(
    llm,
    "shrines.csv",
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

response = agent.run("I am at location 4, -300, 1 where is the closest shrine?")
print(response)
