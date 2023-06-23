import base64
import secrets

from fastapi import (APIRouter, Depends, FastAPI, HTTPException, Request,
                     Security, responses, status)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPDigest
from starlette.datastructures import FormData
from twilio.request_validator import RequestValidator
from utils.generic import logger
from utils.settings_accumalator import Settings


class Routes():
    def __init__(self, settings: Settings):
        self.settings = settings
        self.router = APIRouter()
        self.route_receive_sms = "/sms"

        @self.router.get('/', status_code=status.HTTP_200_OK)
        async def root():
            return {'message': 'coooo'}

        @self.router.post(self.route_receive_sms, dependencies=[Depends(self.authorize_digest)])
        async def receive_sms(request: Request):
            form = await request.form()

            is_signature_valid = self.validate_twilio_signature(request, form)
            if not is_signature_valid:
                logger.info(f'Could not validate signature for incoming request: {form}')
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Twilio signature")
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

    def authorize_digest(self, credentials: HTTPAuthorizationCredentials = Security(HTTPDigest(auto_error=False))):
        incoming_token = credentials.credentials if credentials is not None else ''
        expected_username = self.settings.secrets_app.app_username
        expected_password = self.settings.secrets_app.app_password

        expected_token = base64.standard_b64encode(bytes(f"{expected_username}:{expected_password}", encoding="UTF-8"))
        correct_token = secrets.compare_digest(bytes(incoming_token, encoding="UTF-8"), expected_token)

        if not correct_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect digest token", headers={"WWW-Authenticate": "Digest"})

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
            logger.debug(f'signature expected: {validator.compute_signature(request.url._url, sorted_params)}')
        """
        validator = RequestValidator(self.settings.secrets_twilio.auth_token)
        request_url = request.url._url
        sorted_params = dict(sorted(form.items(), key=lambda x: x[0]))
        twilio_signature_recieved = request.headers.get('X-Twilio-Signature')
        return validator.validate(request_url, sorted_params, twilio_signature_recieved)


class LoggingCORSMiddleware(CORSMiddleware):
    def __init__(self, app: FastAPI, logger: logger):
        super().__init__(app,
                         allow_origins=['*'],
                         allow_credentials=True,
                         allow_methods=['*'],
                         allow_headers=['*'],)
        self.logger = logger

    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        self.logger.info(f"Headers: {headers}")
        await super().__call__(scope, receive, send)
