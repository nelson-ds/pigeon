CURRENT_DIR := $(shell pwd)
ENVIRONMENT := $(shell grep ENVIRONMENT app/configs/.env | cut -d= -f2 | tr -d "'")

start: stop 
	docker-compose up --build -d
	docker logs --follow pigeon_app

stop:
	-docker stop pigeon_app
	-docker rm pigeon_app

twilio-cli:
	docker run -it --rm \
	-v ${CURRENT_DIR}/app/configs/secrets/.twilio-cli.${ENVIRONMENT}:/root/.twilio-cli \
	twilio/twilio-cli bash