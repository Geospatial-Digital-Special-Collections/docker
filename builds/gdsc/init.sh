#!/bin/sh

# load secrets as needed (a sort fo a hack)
cd /home/gdsc

# Copernicus
mkdir -p copernicus
[ -f "copernicus/.cdsapirc" ] && cp copernicus/.cdsapirc ./

# set container waiting
tail -F /dev/null