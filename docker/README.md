# GDSC - Repository Front End  

This repository contains Docker container builds for the GDSC repository front end. Currently there are two implementations:

- GDSC front end (main branch)
- OHDSI front end (ohdsi branch)  

See the docker README for documentation on how to use.

## Build the GDSC front end (a Flask app)  

`$ ./build -r`

Build the docker container for the front end and push to dockerhub. Build takes these options:  

`       -h          to see this help message
       -r          to build repository search interface
       -p          push to dockerhub (defaults to yes)
       -u <user>   specify the user account on dockerhub (optional, defaults to tibben)
       -n <name>   specify the repository name on dockerhub (optional, defaults to pg)`

Runs a variant of these commands:

`cd ../
docker build -t $user/$name:$tag -f ./docker/$tag/Dockerfile .
docker push $user/$name:$tag`

Note, you must be logged into docker hub as `<user>`.