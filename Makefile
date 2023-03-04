build:
	docker build . -t pigeon

start:
	docker run -p 5000:5000 -d --name pigeon pigeon

stop:
	docker stop pigeon
	docker rm pigeon 

