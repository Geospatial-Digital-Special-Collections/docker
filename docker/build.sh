#!/usr/bin/env bash

##
# build.sh
# build docker container images for GDSC 
##

# check to see if running local or the build version of the deployment
tag=0
user='tibben'
name='pg'
push=0
while getopts ":hrpu:n:" option; do
  echo ${option} - ${OPTARG}
  case $option in
    h) # help
       echo 'Usage: $ ./build -hrp -u <user> -n <name>'
       echo 'Options: '
       echo '-h          to see this help message'
       echo '-r          to build repository search interface container '
       echo '-p          to push image to dockerhub (optional, default push=0)'
       echo '-u <user>   specify the user account on dockerhub (optional, default user=tibben)'
       echo '-n <name>   specify the repository name on dockerhub (optional, default name=pg)'
       echo 'NOTE: only one image can be built at a time, build options are exclusive.'
       exit;;
    r) # build the gdsc interface image
       if [[ ${tag} != 0 ]]
       then
         echo 'You cannot use multiple build options.'
         exit
       fi
       tag=repository
       ;;
    p) # push to dockerhub
       push=1
       ;;
    u) # build the gdsc interface image
       user=$OPTARG
       ;;
    n) # build the gdsc interface image
       name=$OPTARG
       ;;
  esac
done

# catch user error for build choice
if [[ ${tag} == 0 ]]
then
  echo 'build.sh error: the build type must be specified'
  echo 'usage:'
  echo './build.sh -h # to see the help message'
  echo './build.sh -r # to build repository search interface'
  echo './build.sh -[r] -p -u <user> -n <name> # specify the user account and repository name for push to dockerhub'
  exit
fi

# build docker image
cd ../
docker build -t $user/$name:$tag -f ./docker/$tag/Dockerfile .
# must be logged into docker hub as $user ($ docker login)

echo $push
if [[ ${push} == 1 ]]
then
  echo docker push $user/$name:$tag
  docker push $user/$name:$tag
fi
