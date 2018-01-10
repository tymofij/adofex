image = "ubuntu:ado"
name = "adofex"

build:
	docker build . --tag $(image)

docker:
	docker run --name $(name) -p 800:800 -v `pwd`:/web/adofex -it $(image)

start:
	@docker container start $(name)

shell:
	@docker exec -i -t $(name) /bin/bash -i -l
