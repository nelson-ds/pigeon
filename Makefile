CURRENT_DIR := $(shell pwd)
ENVIRONMENT := $(shell grep ENVIRONMENT .env | cut -d= -f2 | tr -d "'")

start: stop 
	docker-compose up --build -d
	docker logs --follow pigeon_app

stop:
	-docker stop pigeon_app
	-docker stop mongo_db
	-docker rm pigeon_app
	-docker rm mongo_db

twilio-cli:
	docker run -it --rm \
	-v ${CURRENT_DIR}/secrets/app/${ENVIRONMENT}/twilio/.twilio-cli:/root/.twilio-cli \
	twilio/twilio-cli bash