from logging import getLogger

from fastapi import APIRouter, HTTPException, Request, responses, status
from twilio.request_validator import RequestValidator
from utils.settings_accumalator import Settings

logger = getLogger("uvicorn")


class Routes():
    def __init__(self, settings: Settings):
        self.settings = settings
        self.router = APIRouter()
        self.route_recieve_sms = "/sms"

        @self.router.get('/', status_code=status.HTTP_200_OK)
        async def root():
            return {'message': 'coooo'}

        @self.router.post(self.route_recieve_sms)
        async def receive_sms(request: Request):
            form = await request.form()

            # validator = RequestValidator(self.settings.secrets_twilio.auth_token)
            # webhook_recieve_sms = f"{settings.secrets_app.web_protocol}://{settings.secrets_app.ip_address}/{self.route_recieve_sms}"
            # sorted_params = dict(sorted(form.items(), key=lambda x: x[0]))
            # twilio_signature_recieved = request.headers.get('X-Twilio-Signature')
            # if not validator.validate(webhook_recieve_sms, sorted_params, twilio_signature_recieved):
            #     raise HTTPException(status_code=403, detail="Invalid Twilio signature")

            sms_from = form.get('From')
            sms_body = form.get('Body')
            logger.info(f'Recieved sms from {sms_from} with body" {sms_body}')
            twiml_response = """
                <Response>
                    <Message>Recieved SMS</Message>
                </Response>
            """
            twiml_empty_response = "<Response/>"
            return responses.PlainTextResponse(content=twiml_empty_response, media_type="text/xml")
