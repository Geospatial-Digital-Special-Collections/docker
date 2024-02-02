####################
#
# degauss.py - a simply script to run the degauss geocoder (running as a 
#              kubernetes pod) for an address through the fastAPI library
#
# usage:
# $ curl -G "http://127.0.0.1:8000/geocode/" --data-urlencode 'addr=<some address>'
#
####################

from sys import argv
from yaml import safe_load
from kubernetes import client, config, watch
from kubernetes.stream import stream
from json import dumps as json_dumps
from json import loads as json_loads

from typing import Union
from fastapi import FastAPI

app = FastAPI()

##
 # get postgres credentials
 ##
def get_env():

    with open('kubernetes/secrets/postgis-secret.yaml', 'r') as file: # kmaster.idsc.miami.edu
        env = safe_load(file)['stringData']
    
    return {
        "db": env['POSTGRES_DB'],
        "port": env['POSTGRES_PORT'],
        "user": env['POSTGRES_USER'],
        "pass": env['POSTGRES_PASSWORD']
    }

##
 # get credentialed connection from kube API server and return API objects
 # kmaster.idsc.miami.edu
 ##
def api_config():

    # read token for api access
    with open('kubernetes/secrets/gdsc-controller-token.yaml', 'r') as file:
        secret = safe_load(file)
        
    # create configuration
    gdsc_config = client.Configuration()
    gdsc_config.host = "https://10.141.251.179:6443"
    gdsc_config.ssl_ca_cert = 'kubernetes/pki/server_cert.pem'
    gdsc_config.cert_file = 'kubernetes/pki/client_cert.pem'
    gdsc_config.key_file = 'kubernetes/pki/client_key.pem'
    gdsc_config.verify_ssl = True
    gdsc_config.api_key = {"authorization": "Bearer " + secret['Token']}

    # create api object
    gdsc_client = client.ApiClient(gdsc_config)

    return {
        "cv1": client.CoreV1Api(gdsc_client),
        "av1": client.AppsV1Api(gdsc_client)
    }

##
 # call exec on a pod and give it a shell script
 ##
def pod_exec(api,pod,container,command):
    
    exec_command = [
        '/bin/bash',
        '-c',
        command
    ]
    resp = stream(api["cv1"].connect_get_namespaced_pod_exec,
                  pod,
                  'gdsc',
                  container=container,
                  command=exec_command,
                  stderr=True, stdin=False,
                  stdout=True, tty=False)
    
    return resp

##
 # return names for the PostGIS proxy, osgeo etl, tileserv and other service pods
 # as well as all data pods with associated tablenames
 ##
def get_pods(api,pg):

    services = ["proxy", "osgeo", "tileserv", "solr", "postgrest", "degauss-geocode", "degauss-fastapi", "nominatim", "geoblacklight", "flask"]
    pods = {
        "data": {},
        "service": {}
    }
    response = api["cv1"].list_namespaced_pod(namespace='gdsc')
    for item in response.items:
        service = [service for service in services if (service in item.metadata.name)]
        if (service):
            pods['service'][service[0]] = item.metadata.name
        else:
            sql = "psql -U " + pg['user'] + " -d " + pg['db'] +\
                  " -c \"SELECT tablename FROM pg_catalog.pg_tables" +\
                  " WHERE schemaname != 'pg_catalog'" +\
                  " AND schemaname != 'information_schema'" +\
                  " AND schemaname = 'public'" +\
                  " AND tablename != 'spatial_ref_sys';\""
            resp = pod_exec(api,item.metadata.name,"postgis-node",sql)
            pods['data'][item.metadata.name[0:24]] = {
                "pod": item.metadata.name,
                "table": resp.split('\n')[2].lstrip()
            }

    return pods

##
 # main routine
 ##
pg = get_env()
api = api_config()
pods = get_pods(api,pg)

@app.get("/")
def read_root():
    return {"This": "is not the droid you are looking for"}

@app.get("/geocode/")
def read_geocode(addr: str):
    sh = 'ruby /app/geocode.rb "' + addr + '"'
    response = pod_exec(api,pods['service']['degauss-geocode'],'geocoder',sh).split('\n')
    if (len(response) > 1): response = response[len(response)-2]
    return json_loads(response)