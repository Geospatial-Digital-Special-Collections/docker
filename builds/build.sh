#!/usr/bin/env bash

##
# build.sh
# build docker container images for GDSC 
##

function  showhelp() {
  echo ''
  echo './build.sh'
  echo ''
  echo 'Usage: $ ./build.sh -h[pondr]'
  echo ''
  echo 'Options: '
  echo '-h                  see the help message'
  echo '-p                  build postgis proxy container'
  echo '-n                  build postgis node container'
  echo '-o                  build osgeo/gdal etl container'
  echo '-d                  build degaussAPI container'
  echo '-r                  build gdsc repository interface container'
  echo '-u <user>           dockerhub account username (defaults to: tibben)'
  echo '-b <name>           base name for docker repository (defaults to: pg)'
  echo '--push              push image to dockerhub (optional, default push=0)'
  echo '--multi-platform    make the build multi-platform (arm64 and amd64) (optional, default to host architecture)'
  echo ''
  echo 'NOTE: only one build image can be built at a time, build options are exclusive.'
  echo ''
  echo '--- example ---'
  echo ''
  echo '# build the gdsc repository container and push to docker hub with as tibben/pg:gdsc'
  echo '$ ./build.sh -r -u tibben -b pg --push '
  echo ''
}

function dupfail() {
  echo 'build.sh error: You cannot use multiple build options.'
  echo 'to see usage use: $ ./build.sh -h'
  exit
}

function dedup() {
  if [[ ${tag} != 0 ]]
  then
    dupfail
  fi
}

# check to see if running local or the build version of the deployment
tag=0
user='tibben'
name='pg'
push=0
multi=0
for i in "$@"
do
  p=0
  case "$i" in
 
    --*) # --option
      case "$i" in
        --push) #set push flag to push to dockerhub
          push=1;;
        --multi-platform) #set multi-platform flag
          multi=1;;
      esac
      ;;

    -*) # -option
      case "$i" in
        -h) # help
          showhelp; exit;;
        -p) # build the postgis proxy image
          dedup; tag=proxy;;
        -n) # build the postgis node image
          dedup; subdir='alpine/'; tag=node;;
        -o) # build the osgeo gdal/ogr image
          dedup; tag=osgeo;;
        -d) # build the degauss fastAPI image
          dedup; tag=degaussAPI;;
        -r) # build the gdsc interface image
          dedup; tag=gdsc;;
        -u) # set dockerhub user name
          p=user;;
        -b) # set base name for docker image
          p=name;;
        *) # catch all for duplicate flags
          dupfail;;
      esac
      ;;

    *) # option arguments
      if [ "$p" -ne 0 ]
      then
        eval $p="$i"
      fi
      ;;

  esac
done

# catch user error for build choice
if [[ ${tag} == 0 ]]
then
  echo 'build.sh error: the build type must be specified'
  echo 'to see usage use: $ ./build.sh -h'
  exit
fi

# add GDSC specific content to postGIS scripts
postgis="proxy node"
if [[ "${postgis#*$tag}" != "$postgis" ]]
then
  postgis_version=12-3.3
  sed 's/COPY .\//COPY .\/builds\/'"$tag"'\//g' docker-postgis/$postgis_version/${subdir}Dockerfile > $tag/Dockerfile
  cat $tag/Dockerfile-gdsc >> $tag/Dockerfile
  cat docker-postgis/$postgis_version/${subdir}initdb-postgis.sh $tag/initdb-gdsc.sh > $tag/initdb-postgis.sh
  cat docker-postgis/$postgis_version/${subdir}update-postgis.sh > $tag/update-postgis.sh
fi

# build docker image
if [[ ${multi} == 1 ]]
then
  # build multiple architecture docker image
  list=$(docker buildx ls)
  multi=multi
  if [[ "${list#*$multi}" = "$list" ]]
  then
   docker buildx create -platform linux/arm64,linux/amd64 --name multi
  fi
  docker buildx use multi
  if [[ ${push} == 1 ]]
  then
    docker buildx build --push --platform=linux/amd64,linux/arm64 -t $user/$name:$tag -f ./builds/$tag/Dockerfile .
  else
    docker buildx build --platform=linux/amd64,linux/arm64 -t $user/$name:$tag -f ./builds/$tag/Dockerfile .
  fi
  docker buildx use default
else
  # build single architecture (host) docker image
  cd ../
  docker build -t $user/$name:$tag -f ./builds/$tag/Dockerfile .
fi

# must be logged into docker hub as $user ($ docker login)
if [[ ${push} == 1 ]]
then
  echo docker push $user/$name:$tag
  docker push $user/$name:$tag
fi
