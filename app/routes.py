from logging import getLogger

from fastapi import APIRouter, HTTPException, Request, responses, status
from starlette.datastructures import FormData
from twilio.request_validator import RequestValidator
from utils.settings_accumalator import Settings

logger = getLogger("uvicorn")


class Routes():
    def __init__(self, settings: Settings):
        self.settings = settings
        self.router = APIRouter()
        self.route_receive_sms = "/sms"

        @self.router.get('/', status_code=status.HTTP_200_OK)
        async def root():
            return {'message': 'coooo'}

        @self.router.post(self.route_receive_sms)
        async def receive_sms(request: Request):
            form = await request.form()

            is_signature_valid = self.validate_twilio_signature(request, form)
            if not is_signature_valid:
                logger.info(f'Could not validate signature for incoming request: {form}')
                raise HTTPException(status_code=403, detail="Invalid Twilio signature")
            else:
                logger.debug(f'Signature validated for incoming request: {form}')

            sms_from = form.get('From')
            sms_body = form.get('Body')
            logger.info(f'Recieved sms from {sms_from} with body: " {sms_body}')
            twiml_success_response = """
                <Response>
                    <Message>Recieved SMS</Message>
                </Response>
            """
            twiml_empty_response = "<Response/>"
            return responses.PlainTextResponse(content=twiml_empty_response, media_type="text/xml")

    def validate_twilio_signature(self, request: Request, form: FormData):
        """
        Overview:
            Validates that the webhook is actually being invoked by Twilio
        Args:
            request (Request): The original request sent by Twilio
            form (FormData): The form within the request
        Returns:
            boolean: true if signature can be validated, else false
        Raises:
            N/A
        Example:
            N/A
        Validation:
            print(twilio_signature_recieved, validator.compute_signature(webhook_receive_sms, sorted_params))
        """
        validator = RequestValidator(self.settings.secrets_twilio.auth_token)
        webhook_receive_sms = f"{self.settings.secrets_app.web_protocol}://{self.settings.secrets_app.ip_address}{self.route_receive_sms}"
        sorted_params = dict(sorted(form.items(), key=lambda x: x[0]))
        twilio_signature_recieved = request.headers.get('X-Twilio-Signature')
        return validator.validate(webhook_receive_sms, sorted_params, twilio_signature_recieved)
