# GDSC - Docker Images  

This repository contains Docker container builds for the Geospatial Digital Special Collections tool set. Currently there are two implementations:

- GDSC front end (main branch)
- OHDSI front end (ohdsi branch)  

See the docker README for documentation on how to build and use.

Once built the containers can be run with either docker-compose or kubernetes. 

### Documentation

For most documentation see the README files in respective directories of this repository. 

### postGIS subtree

A git subtree of https://github.com/postgis/docker-postgis is housed in the ```./builds/docker-postgis```. It is used to build the custom postGIS images. The original subtree was added as follows:

```
git remote add -f docker-postgis https://github.com/postgis/docker-postgis.git
git subtree add --prefix builds/docker-postgis docker-postgis master --squash
```

To update the subtree use:

```
$ git fetch docker-postgis master
$ git subtree pull --prefix=docker/docker-postgis docker-postgis master --squash
```

### Questions

Please direct all questions to [mailto:tnorris@miami.edu](tnorris@miami.edu)