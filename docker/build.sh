#!/usr/bin/env bash

##
# build.sh
# build docker container images for GDSC 
##

# check to see if running local or the build version of the deployment
subdir=''
tag=0
user=tibben
name=pg
while getopts ":hrun" option; do
  case $option in
    h) # help
       echo '-h          to see this help message'
       echo '-r          to build repository search interface'
       echo '-u <user>   specify the user account on dockerhub'
       echo '-n <name>   specify the repository name on dockerhub'
       exit;;
    r) # build the gdsc interface image
       tag=repository
       ;;
    u) # build the gdsc interface image
       user=$OPTARG
       ;;
    n) # build the gdsc interface image
       name=$OPTARG
       ;;
  esac
done

# catch user error
if [[ ${tag} == 0 ]]
then
  echo 'build.sh error: the build type must be specified'
  echo 'usage:'
  echo './build.sh -h # to see the help message'
  echo './build.sh -r # to build repository search interface'
  echo './build.sh -r [-u <user> [-n <name>]] # specify the user account and repository name on dockerhub (defaults to tibben/pg)'
  exit
fi

# build docker image
cd ../
docker build -t $user/$name:$tag -f ./docker/$tag/Dockerfile .
# must be logged into docker hub as $user ($ docker login)
# TODO: make idsc dockerhub account
docker push $user/$name:$tag
