from flask import Flask, Response, render_template, request, send_from_directory, url_for, make_response
import gdsc
from urllib.request import urlopen
from urllib.parse import urlencode
import simplejson
import logging
import re
from collections import OrderedDict
import json

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True


##
 # instantiate gdsc
 ##

auth = gdsc.authentication.Auth(env="local-k8s-flask")
pods = gdsc.pod.Pods(api=auth.api, pg=auth.pg)

# get metadata
meta = gdsc.metadata.Meta()
parsed_meta = meta.parse_meta(flavors=["etl","dcat"])

# finally the etl class
loader = gdsc.etl.Etl(
    api = auth.api,
    pg = auth.pg,
    meta = meta,
    pods = pods
)

# get the list of tables on disk
tables = meta.get_all_datasets_on_disk(pods)


##
 # Globals
 ##

BASE_PATH = 'http://gdsc-solr.gdsc:8983/solr'
SNIP_LENGTH = 180
QUERY_FIELDS = ['gdsc_collections', 'dct_title', 'dcat_keyword', 'dct_description', 'gdsc_attributes']
DEFAULT_ROWS = 10
DEBUG = True


##
 # Local functions
 ##

def escape_solr_query(query: str) -> str:
    """
    py:function:: escape_solr_query(query)
    
    Escape characters know to mess with the SOLR query parser

    :param str query: the string to clean
    :return: the cleaned query string
    :rtype: str
    """

    # Solr's reserved syntax characters
    # +, -, &&, ||, !, (, ), {, }, [, ], ^, ~, *, ?, :, \
    pattern = r'[\+\-\&\|\!\(\)\{\}\[\]\^\"\~\*\?\:\\]'
    return re.sub(pattern,'',query)


def query_solr(path: str, parameters: dict, facet_field: str = None) -> tuple:
    """
    py:function:: query_solr(path, parameters, facet_field)

    Query the SOLR API with an index for the catalog or collections.

    :param str path: the base url for the SOLR API
    :param dict parameters: the query parameters
    :param facet_field: optional field for facet counts; if unspecified, queries normally
    :return: the query results, the number of results
    :rtype: tuple
    """

    # Build the query string
    query_string = urlencode(parameters)
    url = f"{path}{query_string}"

    # Send the request
    try:
        with urlopen(url) as connection:
            response = simplejson.load(connection)
    except Exception as e:
        print(f"Error querying SOLR: {e}")
        return [], 0

    # Extract results
    if facet_field is not None:
        if DEBUG: print('getting facets:')
        results = response.get('facet_counts', {}).get('facet_fields', {}).get(facet_field, [])
        numresults = len(results)
    else:
        if DEBUG: print('getting datasets:')
        numresults = response.get('response', {}).get('numFound', 0)
        results = response.get('response', {}).get('docs', [])

    if DEBUG: print(url)
    return results, numresults


##
 # Routes and views
 ##

@app.route('/', methods=["GET"])
def index():
    """ render main page """

    # --- Render ---
    return render_template(
        "index.html",
        pods = pods.pods, 
        meta = parsed_meta,
        tables = tables,
        collections=COLLECTIONS,
        message = ""
    )

@app.route('/load-selected/', methods=["GET"])
def loadform():
    """ load a dataset """

    dataset = request.args.get("dataSelect","")
    print(dataset,"in form")

    return render_template(
        "index.html",
        pods = pods.pods,
        meta = parsed_meta, 
        tables = tables,
        message = {"name": f"{dataset}", "from": "loadform()"}
    )

@app.route('/load/<dataset>', methods=["GET"])
def loadfetch(dataset):
    """ load a dataset """

    print(dataset)

    return {"name": f"{dataset}", "from": "loadFfetch()"}


##
 # always get the list of collections for reference
 ##

COLLECTIONS, COLLECTIONS_COUNT = query_solr(
    f'{BASE_PATH}/collections/select?wt=json&',
    {
      "q.op": "OR",
      "q": "Status:published"
    }
)
keys = [item['CollectionID'][0] for item in COLLECTIONS]
COLLECTIONS = OrderedDict(
    sorted(
        dict(
            zip(keys, COLLECTIONS)).items(), 
            key=lambda i: i[0].lower()
    )
)


##
 # run the app if called from the command line
 ##

if __name__ == '__main__':
    # app.run(host='0.0.0.0')
    app.run(host='0.0.0.0',port=5150,debug=True,use_reloader=True)
