from logging import getLogger

from fastapi import APIRouter, Request, status

router = APIRouter()

logger = getLogger("uvicorn")


@router.get('/', status_code=status.HTTP_200_OK)
async def root():
    return {'message': 'coooo'}


@router.get('/', status_code=status.HTTP_200_OK)
@router.post('/sms')
async def receive_sms(request: Request):
    form = await request.form()
    sms_from = form.get('From')
    sms_body = form.get('Body')
    logger.info(f'Recieved sms from {sms_from} with body" {sms_body}')
