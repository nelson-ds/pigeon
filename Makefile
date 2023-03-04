build:
	docker build . -t pigeon

start:
	docker run -p 5000:5000 -d --name pigeon pigeon

stop:
	docker stop pigeon
	docker rm pigeon 

twilio-cli:
	docker run -it --rm \
	-v ~/repos/pigeon/config/prod/.twilio-cli:/root/.twilio-cli \
	twilio/twilio-cli bash