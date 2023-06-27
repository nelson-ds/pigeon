import base64
import hashlib
import secrets

from fastapi import (APIRouter, Depends, HTTPException, Request, Security,
                     responses, status)
from fastapi.security import (HTTPAuthorizationCredentials, HTTPBasic,
                              HTTPBasicCredentials, HTTPBearer, HTTPDigest)
from starlette.datastructures import FormData
from starlette.types import Message
from twilio.request_validator import RequestValidator
from utils.generic import logger
from utils.settings_accumalator import Settings


class Routes():
    def __init__(self, settings: Settings):
        self.settings = settings
        self.router = APIRouter()
        self.route_receive_sms = "/sms"

        @self.router.get('/pigeon', status_code=status.HTTP_200_OK)
        async def root():
            return {'message': 'coooo'}

        @self.router.post(self.route_receive_sms, dependencies=[Depends(self._authorize)])
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

    def _authorize(self, credentials: HTTPBasicCredentials = Security(HTTPBasic(auto_error=False))):
        logger.info(f'credentialssss: {credentials}')

        # incoming_token = credentials.credentials if credentials is not None else ''

        incoming_username = credentials.username
        incoming_password = credentials.password

        incoming_token = base64.standard_b64encode(bytes(f"{incoming_username}:{incoming_password}", encoding='UTF-8')).decode('UTF-8')

        expected_username = self.settings.secrets_app.app_username
        expected_password = self.settings.secrets_app.app_password
        expected_token = base64.standard_b64encode(bytes(f"{expected_username}:{expected_password}", encoding='UTF-8')).decode('UTF-8')

        correct_token = secrets.compare_digest(incoming_token, expected_token)

        logger.info(f'incoming_token: {incoming_token}')
        logger.info(f'expected_token: {expected_token}')

        if not correct_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect token", headers={'WWW-Authenticate': 'Basic'})

    def _authorize_digest(self, credentials: HTTPAuthorizationCredentials = Security(HTTPDigest(auto_error=False))) -> None:
        incoming_token = credentials.credentials if credentials is not None else ''
        expected_username = self.settings.secrets_app.app_username
        expected_password = self.settings.secrets_app.app_password
        realm = 'TestRealm'

        expected_token = hashlib.md5(f'{expected_username}:{realm}:{expected_password}'.encode('utf-8')).hexdigest()
        logger.info(f'expected_token: {expected_token}')
        correct_token = secrets.compare_digest(incoming_token, expected_token)

        if not correct_token:
            challenge_params = f'Digest realm="{realm}"'
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect digest token",
                headers={"WWW-Authenticate": challenge_params}
            )

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
