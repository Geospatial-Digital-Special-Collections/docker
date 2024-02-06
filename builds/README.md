# GDSC - Docker images for the GDS toolset 

This repository contains the following Docker container builds for the GDSC toolset: Currently there are two implementations:

- GDSC front end (main branch)
- OHDSI front end (ohdsi branch)  

In the main branch the following images are supported:
- postgis proxy
- postgis node
- gdsc repository front end 
- degauss fast api

In development:
- tileserv
- geoblacklight

## Build tool

The script ```./build.sh``` provides a streamlined approach to build all of the different containers and push to dockerhub. Usage:

```./build.sh -h[rpnd] -u <user> -n <name>`

```  
  -h          to see this help message
  -r          to build repository search interface (tag=repository)
  -p          push to dockerhub (defaults to yes)
  -u <user>   specify the user account on dockerhub (optional, user=tibben) 
  -n <name>   specify the repository name on dockerhub (optional, name=pg)
```  

Runs a variant of these commands:

```
cd ../
docker build -t $user/$name:$tag -f ./docker/$tag/Dockerfile .
docker push $user/$name:$tag
```

Note, you must be logged into docker hub as ```<user>```.

## Build the GDSC front end (a Flask app)  

```$ ./build.sh -r```

Build the docker container for the front end and push to dockerhub.

## For arm64 builds on x86-64

- set up QEMU (from https://github.com/docker/buildx/issues/1101)

```$ docker run --rm --privileged tonistiigi/binfmt:latest --install all```