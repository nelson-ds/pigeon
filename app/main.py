from logging import getLogger
from os import environ

from config_loader import ConfigLoader
from dotenv import load_dotenv
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from twilio.rest import Client
from utils import configure_logger
from uvicorn import run

env_path = '/pigeon/.env'

logger = getLogger("uvicorn")
load_dotenv(env_path)
env = environ.get("ENVIRONMENT")
logger.info(f'Setting up config for {env} environment..')
all_configs = ConfigLoader(env).all_configs
uvicorn_reload = all_configs['uvicorn']['reload']
logging_level = all_configs['logging']['level']
twilio_sending_number = all_configs['twilio_sending_number']
twilio_account_sid = all_configs['profiles']['pigeon']['accountSid']
twilio_auth_token = all_configs['profiles']['pigeon']['authToken']
configure_logger(logger, logging_level)


logger.info('Creating Twilio client..')
twilio = Client(twilio_account_sid, twilio_auth_token)

logger.info('Creating fastapi app..')
app = FastAPI()

logger.info('Configure fastapi app..')
origins = ['*']
methods = ['*']
headers = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=methods,
    allow_headers=headers,
)


@app.get('/', status_code=status.HTTP_200_OK)
async def root():
    return {'message': 'coooo'}

if __name__ == '__main__':
    port = int(environ.get('APP_PORT'))
    run('main:app', host='0.0.0.0', port=port, reload=uvicorn_reload)

# FIXME: test local python run
# FIXME: add secrets_template to .gitignore
# TODO: create mongodb with credentials (use automated script)
# TODO: refactor app into modules (use single dotenv)
# TODO: add class for configs
# TODO: add unit tests
# TODO: check mongodb encryption at rest
