from logging import getLogger

from fastapi import APIRouter, Request, responses, status

router = APIRouter()
logger = getLogger("uvicorn")
route_recieve_sms = "/sms"


@router.get('/', status_code=status.HTTP_200_OK)
async def root():
    return {'message': 'coooo'}


@router.post(route_recieve_sms)
async def receive_sms(request: Request):
    form = await request.form()
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
