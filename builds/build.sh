#!/usr/bin/env bash

##
# build.sh
# build docker container images for GDSC 
##

function  showhelp() {
  echo ''
  echo './build.sh'
  echo ''
  echo 'Usage: $ ./build.sh -h[pondr] [-u <user>] [-b <base name>] [--push] [--multi-platform]'
  echo ''
  echo 'Options: '
  echo '-h                  see the help message'
  echo '-p                  build postgis proxy image'
  echo '-n                  build postgis node image'
  echo '-o                  build osgeo/gdal etl image'
  echo '-g                  build gdsc python image'
  echo '-d                  build degaussAPI image'
  echo '-r                  build gdsc repository interface image'
  echo '-u <user>           dockerhub account username (defaults to: tibben)'
  echo '-b <name>           base name for docker repository (defaults to: pg)'
  echo '--push              push image to dockerhub (optional, default push=0)'
  echo '--multi-platform    make the build multi-platform (arm64 and amd64) (optional, default to host architecture)'
  echo ''
  echo 'NOTE: only one build image can be built at a time, build options are exclusive.'
  echo ''
  echo '--- example ---'
  echo ''
  echo '# Build the multi-platform gdsc repository container and push to docker hub as tibben/pg:gdsc.'
  echo '# Assumes you are logged into dockerhub as tibben.'
  echo '$ ./build.sh -r -u tibben -b pg --push --multi-platform'
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
arm=0
for i in "$@"
do
  p=0
  case "$i" in
 
    --*) # --option
      case "$i" in
        --push) # set push flag to push to dockerhub
          push=1;;
        --multi-platform) # set multi-platform flag
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
        -g) # build the python gdsc image
          dedup; tag=gdsc;;
        -d) # build the degauss fastAPI image
          dedup; tag=degaussAPI;;
        -r) # build the gdsc interface image
          dedup; tag=repository;;
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
  postgis_version=15-3.5
  sed 's/COPY .\//COPY .\/builds\/'"$tag"'\//g' docker-postgis/$postgis_version/${subdir}Dockerfile > $tag/Dockerfile
  cat $tag/Dockerfile-gdsc >> $tag/Dockerfile
  cat docker-postgis/$postgis_version/${subdir}initdb-postgis.sh $tag/initdb-gdsc.sh > $tag/initdb-postgis.sh
  cat docker-postgis/$postgis_version/${subdir}update-postgis.sh > $tag/update-postgis.sh
fi

echo pre-build with push=$push and multi=$multi

# build docker image
cd ../
if [[ ${multi} == 1 ]]
then
  # build multiple architecture docker image
  list=$(docker buildx ls)
  multi=multi
  if [[ "${list#*$multi}" = "$list" ]]
  then
   docker buildx create --platform linux/arm64,linux/amd64 --name multi
  fi
  docker buildx use multi
  echo ready to build
  if [[ ${push} == 1 ]]
  then
    # must be logged into docker hub as $user ($ docker login)
    docker buildx build --push --platform=linux/amd64,linux/arm64 -t $user/$name:$tag -f ./builds/$tag/Dockerfile .
  else
    docker buildx build --platform=linux/amd64,linux/arm64 -t $user/$name:$tag -f ./builds/$tag/Dockerfile .
  fi
  docker buildx use default
else
  ptag=$tag
  # a hack to get around difficult multi-architecture builds for postGIS on alpine
  if [[ "$tag" = "node" ]]
  then
    arch=$(uname -a)
    x86=x86_64
    if [[ "${arch#*$x86}" = "$arch" ]]
    then
      ptag=$ptag-arm64
    else
      ptag=$ptag-amd64
    fi
  fi
  # build single architecture (host) docker image
  docker build -t $user/$name:$ptag -f ./builds/$tag/Dockerfile .
  # must be logged into docker hub as $user ($ docker login)
  if [[ ${push} == 1 ]]
  then
    echo docker push $user/$name:$ptag
    docker push $user/$name:$ptag
  fi
fi

cd builds
