from launcher import launcher
from uvicorn import run

if __name__ == '__main__':
    run('launcher:app', host='0.0.0.0', port=launcher.configs.env.app_port_number, reload=launcher.configs.uvicorn.reload)
