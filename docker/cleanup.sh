#!/bin/bash
# General docker cleanup

# first make sure the compose stack is stopped
docker-compose stop

#
# Remove all exited containers
for c in $(docker ps -a -f status=exited -q)
do
	docker rm ${c}
done

# And dangling images
for i in $(docker images -f dangling=true -q)
do
	docker rmi ${i}
done

