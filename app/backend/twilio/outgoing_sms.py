from backend.dto.user_dto import UserDto
from backend.utils.generic import logger
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client as TwilioClient


def send_sms(twilio_client: TwilioClient, from_: str, user: UserDto, body: str):
    is_message_sent = False
    logger.info(f'Sending message: From: {from_}, To: {user.phone_number},  Body: {body}')
    try:
        message = twilio_client.messages.create(
            from_=from_,
            to=user.phone_number,
            body=body
        )
        is_message_sent = True
        logger.info(f'Message sent successfully: ID {message.sid}')
    except TwilioRestException as e:
        logger.error(f"Failed to send message: {e}")
    return is_message_sent
