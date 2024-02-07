# GDSC - GAIA Repository Front End  

This directory contains Docker container builds for the GAIA implementation of the GDSC repository front end.

NOTE: if you are seeking the regular GDSC implementation, please switch your branch to `main`.

## Run the Repository Front End (in this directory)

`$ docker-compose up`

This will build two docker containers locally (if not already built):

- gaia_R: an Ubuntu base container with an R installation including all libraries needed for GAIA (can take a while)  
- gaia_repository: a python Flask base container with a simple search app  

After building the images three containers are run on the gaia-default network (this requires that you have the docker container for the GAIA database already running).

- gaia-R
- gaia-repository
- gaia-solr

Notes:  

- The gaia-solr container will create a docker managed volume called gaia-solr-index where the index will be stored.
- The gaia-solr container needs a collections directory in this location (where the json metadata is stored). If this does not yet exist, you must create it Iit will be ignored by git).
- You must refresh the json with the R based tool ...