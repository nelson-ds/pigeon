from fastapi import HTTPException, Request
from routes import route_recieve_sms
from twilio.request_validator import RequestValidator

from app.utils.settings_accumalator import Settings


def validate_twilio_signature(settings: Settings, request: Request):
    validator = RequestValidator(settings.secrets_twilio.auth_token)
    webhook_recieve_sms = f"{settings.secrets_app.web_protocol}://{settings.secrets_app.ip_address}/{route_recieve_sms}"
    twilio_signature_recieved = request.headers.get('X-Twilio-Signature')
    if not validator.validate(webhook_recieve_sms, request, twilio_signature_recieved):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
