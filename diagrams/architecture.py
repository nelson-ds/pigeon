from diagrams import Diagram, Edge
from diagrams.custom import Custom
from diagrams.generic.device import Mobile
from diagrams.onprem.compute import Server
from diagrams.onprem.database import Mongodb
from diagrams.saas.communication import Twilio

with Diagram("Architecture", show=False):
    custom_image_langchain = "diagrams/logos/langchain.png"
    custom_image_open_ai = "diagrams/logos/open_ai.png"
    custom_image_chroma_db = "diagrams/logos/chroma_db.png"

    pigeon_server = Server("FastApi Server")
    mongo_db = Mongodb("MongoDB")
    twilio = Twilio("Twilio")
    user = Mobile("User")

    chroma_db = Custom("VectorDB", custom_image_chroma_db)
    langchain = Custom("AI\nOrchestration", custom_image_langchain)
    open_ai = Custom("AI Model", custom_image_open_ai)

    mongo_db >> Edge(forward=True, reverse=True) >> pigeon_server

    pigeon_server >> Edge(forward=True, reverse=True) >> twilio
    twilio >> Edge(forward=True, reverse=True, label="SMS") >> user
    langchain >> Edge(forward=True, reverse=True) >> open_ai
    pigeon_server >> Edge(forward=True, reverse=True) >> langchain
    chroma_db >> langchain
