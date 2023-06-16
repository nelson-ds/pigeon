CURRENT_DIR := $(shell pwd)
ENVIRONMENT := $(shell grep ENVIRONMENT .env | cut -d= -f2 | tr -d "'")

start: stop 
	docker-compose up --build -d
	docker logs --follow pigeon_app

stop:
	-docker stop pigeon_app
	-docker stop mongodb
	-docker rm pigeon_app
	-docker rm mongodb

twilio-cli:
	docker run -it --rm \
	-v ${CURRENT_DIR}/secrets/${ENVIRONMENT}/twilio/.twilio-cli:/root/.twilio-cli \
	twilio/twilio-cli bash