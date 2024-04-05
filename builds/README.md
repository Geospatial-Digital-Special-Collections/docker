# GDSC - Docker images for the GDS toolset 

This repository contains the following Docker container builds for the GDSC toolset: Currently there are two implementations:

- GDSC front end (main branch)
- OHDSI front end (ohdsi branch)  

In the main branch the following images are supported:
- postgis proxy
- postgis node
- osgeo/gdal ETL 
- repository front end 
- degauss fast api

In development:
- tileserv
- geoblacklight

## Build tool

The script ```./build.sh``` provides a streamlined approach to build all of the different containers and push to dockerhub. Usage:

```
./build.sh

Usage: $ ./build.sh -h[pondr] [-u <user>] [-b <base name>] [--push] [--multi-platform]

Options: 
-h                  see the help message
-p                  build postgis proxy container
-n                  build postgis node container
-o                  build osgeo/gdal etl container
-d                  build degaussAPI container
-r                  build gdsc repository interface container
-u <user>           dockerhub account username (defaults to: tibben)
-b <name>           base name for docker repository (defaults to: pg)
--push              push image to dockerhub (optional, default push=0)
--multi-platform    make the build multi-platform (arm64 and amd64) (optional, default to host architecture)

NOTE: only one build image can be built at a time, build options are exclusive.

--- example ---

# Build the multi-platform gdsc repository container and push to docker hub as tibben/pg:gdsc.
# Assumes you are logged into dockerhub as tibben.
$ ./build.sh -r -u tibben -b pg --push --multi-platform
```  

Runs a variant of these commands for a single architecture build:

```
cd ../
docker build -t $user/$name:$tag -f ./docker/$tag/Dockerfile .
docker push $user/$name:$tag
```

or these for a multi-architecture build

```
cd ../
docker buildx build --push --platform=linux/amd64,linux/arm64 -t $user/$name:$tag -f ./docker/$tag/Dockerfile .
```

Note, you must be logged into docker hub as ```<user>``` for the push to work.

## For arm64 builds on x86-64

- set up QEMU (from https://github.com/docker/buildx/issues/1101)

```$ docker run --rm --privileged tonistiigi/binfmt:latest --install all```