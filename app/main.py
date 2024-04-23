from backend.utils.generic import custom_logger
from launcher import launcher
from uvicorn import run

if __name__ == '__main__':
    run(
        'launcher:app',
        host='0.0.0.0',
        port=launcher.settings.configs_env.app_port_number,
        reload=launcher.settings.configs_app.uvicorn_reload,
        log_config=custom_logger.logging_config
    )
