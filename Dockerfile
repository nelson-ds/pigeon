FROM python:3.11.2-slim

WORKDIR  /pigeon/app/

RUN pip install --no-cache-dir -U pip

COPY /app/configs/requirements.txt /tmp/

RUN pip install --no-cache-dir -r /tmp/requirements.txt

CMD ["python", "main.py"]