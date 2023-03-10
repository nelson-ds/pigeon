from logging import getLogger
from os import environ

from config_loader import ConfigLoader
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from twilio.rest import Client
from utils import configure_logger
from uvicorn import run

logger = getLogger("uvicorn")

logger.info("Setting up config..")
all_configs = ConfigLoader().all_configs
uvicorn_reload = all_configs["uvicorn"]["reload"]
logging_level = all_configs["logging"]["level"]
twilio_phn_from = all_configs["twilio"]["phn_from"]
twilio_phn_to = all_configs["twilio"]["phn_to"]
twilio_account_sid = all_configs["profiles"]["pigeon"]["accountSid"]
twilio_auth_token = all_configs["profiles"]["pigeon"]["authToken"]
configure_logger(logger, logging_level)


logger.info("Creating Twilio client..")
twilio = Client(twilio_account_sid, twilio_auth_token)

logger.info("Creating fastapi app..")
app = FastAPI()

logger.info("Configure fastapi app..")
origins = ["*"]
methods = ["*"]
headers = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=methods,
    allow_headers=headers,
)


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "coooo"}

if __name__ == "__main__":
    port = int(environ.get("PORT", 5000))
    run("main:app", host="0.0.0.0", port=port, reload=uvicorn_reload)
