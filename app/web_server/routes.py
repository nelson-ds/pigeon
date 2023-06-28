from communication.incoming_sms import IncomingSms
from data_models.dao.mongodb_dao import MongodbDao
from fastapi import (APIRouter, Depends, HTTPException, Request, Security,
                     responses, status)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.datastructures import FormData
from twilio.request_validator import RequestValidator
from twilio.rest import Client as TwilioClient
from utils.generic import logger
from utils.settings_accumalator import Settings


class Routes():
    def __init__(self, settings: Settings, twilio_client: TwilioClient, mongodb_dao: MongodbDao):
        self.settings = settings
        self.twilio_client = twilio_client
        self.mongodb_dao = mongodb_dao
        self.router = APIRouter()
        self.route_receive_sms = "/sms"

        @self.router.get('/pigeon', status_code=status.HTTP_200_OK)
        async def root():
            return {'message': 'coooo'}

        @self.router.post(self.route_receive_sms, dependencies=[Depends(self._authorize)])
        async def receive_sms(request: Request):
            form = await request.form()
            self.validate_twilio_signature(request, form)
            sms_from, sms_body = form.get('From'), form.get('Body')
            logger.info(f'Recieved sms from {sms_from} with body: {sms_body}')
            incoming_sms = IncomingSms(sms_from, sms_body, mongodb_dao)
            response = incoming_sms.get_response()
            return responses.PlainTextResponse(content=response, media_type="text/xml")

    def _authorize(self, credentials: HTTPBasicCredentials = Security(HTTPBasic(auto_error=False))):
        incoming_username = credentials.username if credentials else ''
        incoming_password = credentials.password if credentials else ''
        expected_username = self.settings.secrets_app.app_username
        expected_password = self.settings.secrets_app.app_password
        correct_token = incoming_username == expected_username and incoming_password == expected_password
        if not correct_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials", headers={'WWW-Authenticate': 'Basic'})

    def validate_twilio_signature(self, request: Request, form: FormData):
        """
        Overview:
            Validates that the webhook is actually being invoked by Twilio
        Args:
            request (Request): The original request sent by Twilio
            form (FormData): The form within the request
        Raises:
            HTTPException
        Validation:
            logger.debug(f'signature expected: {validator.compute_signature(request.url._url, sorted_params)}')
        """
        validator = RequestValidator(self.settings.secrets_twilio.auth_token)
        request_url = request.url._url
        sorted_params = dict(sorted(form.items(), key=lambda x: x[0]))
        twilio_signature_recieved = request.headers.get('X-Twilio-Signature')
        is_signature_valid = validator.validate(request_url, sorted_params, twilio_signature_recieved)
        if not is_signature_valid:
            logger.info(f'Could not validate signature for incoming request: {form}')
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Twilio signature")
        else:
            logger.debug(f'Signature validated for incoming request: {form}')
