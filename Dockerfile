FROM python:3.9.13-alpine

WORKDIR  /pigeon/app/

RUN pip install --no-cache-dir -U pip

COPY /app/requirements.txt /tmp/

RUN pip install --no-cache-dir -r /tmp/requirements.txt

CMD ["python", "main.py"]