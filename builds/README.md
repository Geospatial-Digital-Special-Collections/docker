# GDSC - Repository Front End  

This folder contains Docker container builds for the gaia implementation of the GDSC repository front end.

NOTE: if you are seeking the regular GDSC implementation, please switch your branch to `main`.

## Run the Repository Front End (in this directory)

`$ docker-compose up`

This will build two docker containers locally (if not already built):

- gaia_R: an Ubuntu base container with an R installation including all libraries needed for gaia (can take a while)  
- gaia_repository: a python Flask base container with a simple search app  

After building the images three containers are run on the gaia-default network (this requires that you have the docker container for the gaia database already running).

- gaia-R
- gaia-repository
- gaia-solr

Notes:  

- The gaia-solr container will create a volume called gaia-solr-index where the index will be stored.
- The gaia-solr container needs the collections folder (where the json metadata is stored).
- You must refresh the json with the R based tool ...