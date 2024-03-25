from back_end.dao.mongodb_dao import MongodbDao
from back_end.langchain.llm_client import LangchainClient
from back_end.twilio.incoming_sms import IncomingSms
from back_end.utils.generic import logger
from back_end.utils.settings_accumalator import Settings
from fastapi import (APIRouter, Depends, HTTPException, Request, Security,
                     responses, status)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from starlette.datastructures import FormData
from twilio.request_validator import RequestValidator
from twilio.rest import Client as TwilioClient


class Routes():
    def __init__(self, settings: Settings, mongodb_dao: MongodbDao, twilio_client: TwilioClient, langchain_client: LangchainClient):
        self.settings = settings
        self.router = APIRouter()
        self.templates = Jinja2Templates(directory=self.settings.configs_app.web_templates_dir)

        @self.router.get(self.settings.configs_app.web_route_home)
        async def get_home(request: Request):
            return self.templates.TemplateResponse(self.settings.configs_app.web_template_home_file_name, {'request': request})

        @self.router.post(self.settings.configs_app.web_route_sms, dependencies=[Depends(self._authorize)])
        async def receive_sms(request: Request):
            form = await request.form()
            self.validate_twilio_signature(request, form)
            sms_from, sms_body = form.get('From'), form.get('Body')
            logger.info(f'Recieved sms from {sms_from} with body: {sms_body}')
            incoming_sms = IncomingSms(settings, mongodb_dao, langchain_client, sms_from, sms_body)
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
            logger.debug(f'signature expected: {validator.compute_signature(request_url, sorted_params)}')
        """
        if self.settings.configs_env.environment != 'dev':
            validator = RequestValidator(self.settings.secrets_twilio.auth_token)
            request_url = self.get_url(request)
            sorted_params = dict(sorted(form.items(), key=lambda x: x[0]))
            twilio_signature_recieved = request.headers.get('X-Twilio-Signature')
            is_signature_valid = validator.validate(request_url, sorted_params, twilio_signature_recieved)
            if not is_signature_valid:
                logger.info(f'Could not validate signature for incoming request: {form}')
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Twilio signature")
            else:
                logger.debug(f'Signature validated for incoming request: {form}')

    def get_url(self, request: Request):
        """
        Get the URI from the request and handles cases where the request is forwarded from reverse proxy
        :param request: The request from Twilio
        :returns: The URL of the request
        :rtype: str
        """
        url = request.url._url
        original_protocol = request.headers.get("X-Forwarded-Proto", default="")
        if original_protocol:
            url = f"{original_protocol}://{request.headers['host']}{request.url.path}"  # construct the URL using the original protocol
        return url
