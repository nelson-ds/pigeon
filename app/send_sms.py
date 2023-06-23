from logging import getLogger

from twilio.rest import Client
from utils.generic import logger


def send_sms(twilio_client: Client, from_: str, to: str):

    message = twilio_client.messages.create(
        from_=from_,
        to=to,
        body="Coo Coo"
    )

    logger.info(f"sending message: {message.body}, from: {message.from_}, to: {message.to}")
