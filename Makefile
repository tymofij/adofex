image = "ubuntu:17.10"
name = "adofex"

docker:
	docker run --name $(name) -p 3000:3000 -p 8080:8080 -v `pwd`:/web/adofex -v ~/projects/indifex:/web/indifex -it $(image)

start:
	@docker container start $(name)

shell:
	@docker exec -i -t $(name) /bin/bash -i -l
