from launcher import launcher
from uvicorn import run

if __name__ == '__main__':
    run('launcher:app', host='0.0.0.0', port=launcher.configs.uvicorn.port, reload=launcher.configs.uvicorn.reload)
