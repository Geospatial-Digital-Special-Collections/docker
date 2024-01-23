#!/usr/bin/env bash

##
# build.sh
# build docker container images for GDSC 
##

# check to see if running local or the build version of the deployment
tag=0
user='ohdsi'
name='gaia-catalog'
push=0
while getopts ":hrsRp:u:n" option; do
  case $option in
    h) # help
       echo 'Usage: $ ./build -hrsRp -u <user> -n <name>'
       echo 'Options: '
       echo '-h          to see this help message'
       echo '-r          to build repository search interface container '
       echo '-s          to build solr container for indexing'
       echo '-R          to build R container for connecting to gaia database'
       echo '-p          to push image to dockerhub (optional, defaults to no)'
       echo '-u <user>   specify the user account on dockerhub (optional, default=ohdsi)'
       echo '-n <name>   specify the repository name on dockerhub (optional, default=gaia-catalog)'
       echo 'NOTE: only one image can be built at a time, options -rsR are exclusive and cannot be used together.'
       exit;;
    r) # build the gdsc interface image
       if [[ ${tag} != 0 ]]
       then
         echo 'You cannot use options -rsR together.'
         exit
       fi
       tag=repository
       ;;
    s) # build the solr indexing image
       if [[ ${tag} != 0 ]]
       then
         echo 'You cannot use options -rsR together.'
         exit
       fi
       tag=solr
       ;;
    R) # build the gaia R image
       if [[ ${tag} != 0 ]]
       then
         echo 'You cannot use options -rsR together.'
         exit
       fi
       tag=R
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
  echo './build.sh -s # to build solr container for indexing'
  echo './build.sh -R # to build R container for indexing'
  echo './build.sh -[rsR] -p -u <user> -n <name> # specify the user account and repository name for push to dockerhub'
  exit
fi

# build docker image
cd ../
docker build -t $user/$name:$tag -f ./docker/$tag/Dockerfile .
# must be logged into docker hub as $user ($ docker login)
if [[ ${push} == 1 ]]
then
  docker push $user/$name:$tag
fi
