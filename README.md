# pigeon
Serendipitious intermittent message delivery service

## Development Environment

### Dependencies
1. [Docker](https://www.docker.com/) needs to be installed
2. [Make](https://www.gnu.org/software/make/) needs to be installed

### Setting up development environment (optional, to provide python linting)
1. Create python virtual environment: `pyenv virtualenv 3.9.10 py39_pigeon`
2. Install python libraries in the newly created environment: `pip install -r requirements.txt`

### Working in development environment
1. Build the application (one time): `make build`
2. Start the application: `make start`
3. Stop the application: `make stop`