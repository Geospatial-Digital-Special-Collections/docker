##
# build.ps1
# build docker container images for GDSC 
##

function showhelp {
	Write-Host ''
  Write-Host './build.sh'
  Write-Host ''
  Write-Host 'Usage: $ ./build.sh -h[pondr] [-u <user>] [-b <base name>] [--push] [--multi-platform]'
  Write-Host ''
  Write-Host 'Options: '
  Write-Host '-h                  see the help message'
  Write-Host '-p                  build postgis proxy container'
  Write-Host '-n                  build postgis node container'
  Write-Host '-o                  build osgeo/gdal etl container'
  Write-Host '-d                  build degaussAPI container'
  Write-Host '-r                  build gdsc repository interface container'
  Write-Host '-u <user>           dockerhub account username (defaults to: tibben)'
  Write-Host '-b <name>           base name for docker repository (defaults to: pg)'
  Write-Host '--push              push image to dockerhub (optional, default push=0)'
  Write-Host '--multi-platform    make the build multi-platform (arm64 and amd64) (optional, default to host architecture)'
  Write-Host ''
  Write-Host 'NOTE: only one build image can be built at a time, build options are exclusive.'
  Write-Host ''
  Write-Host '--- example ---'
  Write-Host ''
  Write-Host '# Build the multi-platform gdsc repository container and push to docker hub as tibben/pg:gdsc.'
  Write-Host '# Assumes you are logged into dockerhub as tibben.'
  Write-Host '$ ./build.sh -r -u tibben -b pg --push --multi-platform'
  Write-Host ''
}

function dupfail {
  Write-Host 'build.sh error: You cannot use multiple build options.'
  Write-Host 'to see usage use: $ ./build.sh -h'
  exit
}

function dedup() {
  if ( $tag -ne 0 ) {
    dupfail
  }
}

# check to see if running local or the build version of the deployment
$tag=0
$user='tibben'
$name='pg'
$push=0
$multi=0
$arm=0

for ( $i = 0; $i -lt $args.count; $i++ ) {
  $p = 0
  switch($args[$i]) {
  	{ $_ -Match "--" } { 
  		switch($args[$i]) {
  			"--push" { $push=1; Break }
  			"--multi-platform" { $multi=1; Break }
  		}
  		Break
  	}
  	{ $_ -Match "-" } {
  		switch($args[$i]) {
        "-h" { showhelp; Break } # help
        "-p" { dedup; $tag="proxy"; Break }
        "-n" { dedup; $subdir="alpine/"; $tag="node"; Break }
        "-o" { dedup; $tag="osgeo"; Break }
        "-d" { dedup; $tag="degaussAPI"; Break }
        "-r" { dedup; $tag="repository"; Break }
        "-u" { $p=$user; Break }
        "-b" { $p=$name; Break }
        default { dupfail; Break }
  		}
  		Break
  	}
  	default {
  		if ($p -ne 0) { $p = $args[$i] }
  	}
  }
}

if ( $tag -eq 0 ) {
	Write-Host 'build.sh error: the build type must be specified'
  Write-Host 'to see usage use: $ ./build.sh -h'
  exit
}

Write-Host "tag: " $tag
Write-Host "user: " $user
Write-Host "name: " $name
Write-Host "push: "$push
Write-Host "multi: " $multi
Write-Host "arm: " $arm

# add GDSC specific content to postGIS scripts
$postgis="proxy node"
if ( $postgis -Match $tag ) {
  $postgis_version="12-3.4"
  (gc docker-postgis/$postgis_version/${subdir}Dockerfile) -replace "COPY .", "COPY ./builds/$tag" > $tag/Dockerfile
  gc $tag/Dockerfile-gdsc >> $tag/Dockerfile
  gc docker-postgis/$postgis_version/${subdir}initdb-postgis.sh, $tag/initdb-gdsc.sh > $tag/initdb-postgis.sh
  gc docker-postgis/$postgis_version/${subdir}update-postgis.sh > $tag/update-postgis.sh
}

Write-Host "pre-build with push="$push" and multi="$multi

# build docker image
cd ../
if ( $multi -eq 1 ) {

  # build multiple architecture docker image
  $list = (docker buildx ls)
  $multi = "multi"
  if ( $list -Match $multi ) {
    docker buildx create --platform linux/arm64,linux/amd64 --name multi
  }
  docker buildx use multi
  Write-Host "ready to build"
  if ( $push -eq 1 ) {
    # must be logged into docker hub as $user ($ docker login)
    docker buildx build --push --platform=linux/amd64,linux/arm64 -t $user/${name}:${tag} -f ./builds/$tag/Dockerfile .
  } else {
    docker buildx build --platform=linux/amd64,linux/arm64 -t $user/${name}:${tag} -f ./builds/$tag/Dockerfile .
  }
  docker buildx use default
} else {
  $ptag = $tag
  # a hack to get around difficult multi-architecture builds for postGIS on alpine
  if ( $tag -eq "node" ) {
    $arch=(Get-CimInstance -ClassName Win32_Processor)
    $x86="Intel64"
    if ( $arch -Match $x86 ) {
      $ptag="${ptag}-arm64"
    } else {
      $ptag="$ptag-amd64"
    }
  }
  # build single architecture (host) docker image
  docker build -t $user/${name}:${ptag} -f ./builds/$tag/Dockerfile .
  # must be logged into docker hub as $user ($ docker login)
  if ( $push -eq 1 ) {
    Write-Host "docker push $user/${name}:${ptag}"
    docker push $user/${name}:${ptag}
  }
}

cd builds