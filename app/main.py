from os import environ

from fastapi import FastAPI
from launcher import Launcher
from uvicorn import run

launcher = Launcher()
app = FastAPI()
launcher.configure_app(app)


if __name__ == '__main__':
    port = int(environ.get('APP_PORT'))
    run('main:app', host='0.0.0.0', port=port, reload=launcher.configs.uvicorn.reload)
