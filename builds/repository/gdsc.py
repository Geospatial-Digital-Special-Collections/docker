from flask import Flask, Response, render_template, request, send_from_directory, url_for, make_response
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

BASE_PATH = 'http://gdsc-solr.gdsc:8983/solr'
SNIP_LENGTH = 180
QUERY_FIELDS = ['gdsc_collections','dct_title','dcat_keyword','dct_description','gdsc_attributes']
DEFAULT_ROWS = 10

FILTER_SPECS = {
    "keyword": {
        "field": "dcat_keyword",
        "facet_name": "possible_keywords"
    },
    "geometry": {
        "field": "locn_geometry",
        "facet_name": "possible_geometries"
    },
    "representation": {
        "field": "adms_representationTechnique",
        "facet_name": "possible_representations"
    },
    "right": {
        "field": "dct_rights",
        "facet_name": "possible_rights"
    },
    "active": {
        "field": "gdsc_up",
        "facet_name": "possible_activity"
    }
}

##
 # Local functions
 ##


def query_solr(path: str, parameters: dict, facet_field: str = None) -> tuple:
    """
    Query the SOLR API with an index for the catalog or collections.

    :param str path: the base url for the SOLR API
    :param dict parameters: the query parameters
    :param facet_field: optional field for which to get all possible options for froma all documents, if unspecified, query normally
    :return: the query results, the number of results
    :rtype: tuple
    """

    # Build the query string
    query_string = urlencode(parameters).replace('-', '+')
    url = f"{path}{query_string}"
    print(url)

    # Send the request
    try:
        with urlopen(url) as connection:
            response = simplejson.load(connection)
    except Exception as e:
        print(f"Error querying SOLR: {e}")
        return [], 0

    # Extract results
    if facet_field != None:
        results = response.get('facet_counts', {}).get('facet_fields', {}).get(facet_field, [])
        numresults = len(results)
        print("getting facets")
    else:
        numresults = response.get('response', {}).get('numFound', 0)
        results = response.get('response', {}).get('docs', [])

    return results, numresults


def highlight_query(document: dict, query: str) -> dict:
    """
    py:function:: query_solr(path, parameters)

    Highlight the query text in the given document.

    :param dict document: the document metadata
    :param str query: string to highlight in the document
    :return: the document metadata with css class elements added to html content in dict entries found in QUERY_FIELDS
    :rtype: dict
    """

    def add_tags(string_value,query):
        return re.sub(
            r'(' + term  + ')',
            '<span class="highlight-term">\g<1></span>',
            string_value,
            flags=re.IGNORECASE)

    document['found_in'] = {}
    for field in QUERY_FIELDS:
        if field in document:
            attrs = []
            for i, attr in enumerate(document[field]):
                terms = query.split(' ')
                found = True
                for term in terms:
                    if term.upper() not in attr.upper(): found = False
                if found:
                    document['found_in'][field] = []
                    for term in terms:
                        document[field][i] = add_tags(document[field][i],term)
                    row = attr.split(';')
                    if len(row) > 1:
                        document[field][i] = add_tags(document[field][i],row[0])
                        for j in range(0,2):
                            for term in terms:
                                row[j] = add_tags(row[j],term)
                        row[0] = add_tags(row[0],row[0])
                        attrs.append([row[0],row[1]])
            if len(attrs) > 0: document['found_in'][field] = attrs

    return document


def build_citation(document: dict, type: str) -> str:
    """
    py:function:: build_citation(document, type)

    Create a formatted citation string for the document in the given format type.

    :param dict document: the document metadata
    :param str type: the format type ["bibtex", "ris"]
    :return: the formatted ciatation
    :rtype: str
    """

    cite_formats = {
        "formatters": {
            "bibtex": {
                "begin": "@misc{",
                "indent": "  ",
                "seperator": " = ",
                "quote_start": "{",
                "quote_end": "}",
                "line_seperator": ",",
                "end": "}"
            },
            "ris": {
                "begin": "TY  - DATA\n",
                "indent": "",
                "seperator": "  - ",
                "quote_start": "",
                "quote_end": "",
                "line_seperator": "",
                "end": "ER  - \n\n"
            }
        },
        "extension": {
            "bibtex": "bib",
            "ris": "ris"
        },
        "fields" : {
            "dct_creator": {
                "type": "list",
                "bibtex": "author",
                "ris": "AU"
            },
            "dct_issued": {
                "type": "date",
                "bibtex": "year",
                "ris": "PY"
            },
            "dct_title": {
                "type": "single",
                "bibtex": "title",
                "ris": "TI"
            },
            "dct_publisher": {
                "type": "single",
                "bibtex": "publisher",
                "ris": "PB"
            },
            "dct_identifier": {
                "type": "single",
                "bibtex": "url",
                "ris": "UR"
            },
            "dcat_keyword": {
                "type": "list",
                "bibtex": "keywords",
                "ris": "KW"
            },
            "dct_modified": {
                "type": "date",
                "bibtex": "timestamp",
                "ris": "Y2"
            },
            "dct_language": {
                "type": "single",
                "bibtex": "language",
                "ris": "LA"
            },
            "gdsc_version": {
                "type": "single",
                "ris": "WV"
            },
            "gdsc_collections": {
                "type": "single",
                "ris": "T3"
            }
        }
    }

    def build_element(field,value):
        return (
            f"{formatters['indent']}{field}{formatters['seperator']}"
            f"{formatters['quote_start']}{value}{formatters['quote_end']}"
            f"{formatters['line_seperator']}\n"
        )

    formatters = cite_formats['formatters'][type]
    entry = formatters['begin']
    if type == "bibtex":
        entry += f"{document['gdsc_tablename'][0]}\n" or "citation\n"

    formatters = cite_formats['formatters'][type]
    # looped citation body construction
    for dc_term in cite_formats['fields']:
        field = cite_formats['fields'][dc_term]
        if type in field:
            if dc_term in document:
                val = document[dc_term]       
                if field['type'] in ["single", "date"]:
                    if dc_term in ["dct_issued"]: val[0] = val[0][:4]
                    if dc_term in ["dct_modified"]: val[0] = val[0].split('T')[0]    
                    entry += build_element(field[type],val[0])
                elif field['type'] == "list":
                    for item in val:
                        entry += build_element(field[type],item.split(";")[0])

    entry += formatters['end']
    return entry


def build_filter_clause(field, values):
    if not values:
        return ""

    clauses = [f'{field}:"{v}"' for v in values]
    return f" ({' AND '.join(clauses)})"

def fetch_facets(field, query, fq):
    params = {
        "q": query,
        "fq": fq,
        "facet.field": field,
        "indent": "true",
        "q.op": "AND",
        "rows": "0",
        "facet": "true"
    }

    return query_solr(
        f'{BASE_PATH}/dcat/select?wt=json&',
        params,
        field
    )

##
 # run SOLR query and render results for main page
 ##
@app.route('/', methods=["GET"])
def index():

    collection = request.args.get("collection", "all")
    query = request.args.get("query", "")
    page = int(request.args.get("page", 1))

    # --- Collect filters dynamically ---
    selected_filters = {
        key: request.args.getlist(key)
        for key in FILTER_SPECS
    }

    # --- Base query ---
    q = query or "*"

    fq_parts = []

    if collection == "all":
        fq_parts.append("gdsc_collections:*")
    else:
        fq_parts.append(f'gdsc_collections:"{collection}"')

    # --- Apply programmatic filters ---
    for key, values in selected_filters.items():
        field = FILTER_SPECS[key]["field"]
        clause = build_filter_clause(field, values)
        if clause:
            fq_parts.append(clause)

    fq = " ".join(fq_parts)

    # --- Solr query ---
    query_parameters = {
        "q.op": "AND",
        "defType": "edismax",
        "fq": fq,
        "q": q,
        "qf": ' '.join(QUERY_FIELDS),
        "start": (page - 1) * DEFAULT_ROWS,
        "rows": DEFAULT_ROWS
    }

    results, numresults = query_solr(
        f'{BASE_PATH}/dcat/select?wt=json&',
        query_parameters
    )

    # --- Post-processing ---
    for entry in results:

        if query:
            entry = highlight_query(entry, query)

        if entry.get('dct_description'):
            desc = entry['dct_description'][0]
            entry['display_description'] = (
                desc[:SNIP_LENGTH] + '...'
                if len(desc) > SNIP_LENGTH else desc
            )

    if collection == "*":
        collection = "all"

    # --- Fetch facet values dynamically ---
    facet_data = {}

    for key, spec in FILTER_SPECS.items():
        values, count = fetch_facets(spec["field"], q, fq)
        facet_data[spec["facet_name"]] = values

    # --- Render ---
    return render_template(
        "index.html",
        collection=collection,
        query=query,
        page=page,
        results=results,
        numresults=numresults,
        collections=COLLECTIONS,
        root="./",
        **selected_filters,
        **facet_data
    )

##
 # query SOLR for one document and render all metadata in detail
 ##
@app.route('/detail/<name_id>', methods=["GET","POST"])
def detail(name_id):

    args = request.args.to_dict()

    query_parameters = {"q": "gdsc_tablename:" + name_id}
    query_string  = urlencode(query_parameters)
    connection = urlopen("{}{}".format(f'{BASE_PATH}/dcat/select?wt=json&', query_string))
    response = simplejson.load(connection)
    document = response['response']['docs'][0]

    if "query" in args:
        if args['query'] != None and args['query'] != 'None' and args['query'] != '':
            document = highlight_query(document,args['query'])
    else: args['query'] = None

    if 'gdsc_attributes' in document:
        document['gdsc_columns'] = [attr.split(';')[0] for attr in document['gdsc_attributes']]

    if 'gdsc_attributes' in document:
        document['gdsc_attributes'] = [attr.split(';') for attr in document['gdsc_attributes']]

    if 'gdsc_derivatives' in document:
        document['gdsc_derived'] = [attr.split(';') for attr in document['gdsc_derived']]

    # get json_ld 
    with open(f"/data/{name_id}/meta_json-ld_{name_id}.json", 'r', encoding='utf-8') as f:
        json_ld = json.load(f)
        
    # render page
    return render_template(
        'detail.html', 
        name_id=name_id, 
        document=document, 
        referrer=args,
        root='../',
        json_ld=json_ld
    )

@app.route('/bibliography/<collection>/<fmt>', methods=["GET"])
@app.route('/cite/<table_id>/<fmt>', methods=["GET"])
def cite(collection=None, table_id=None, fmt=None):
    # Normalize parameters
    name_id = table_id  # reuse variable name for clarity

    # Build query parameters
    if name_id:
        query_parameters = {"q": f"gdsc_tablename:{name_id}"}
    elif collection:
        if collection == "all":
            query_parameters = {"q": "*:*"}
        else:
            query_parameters = {"q": f"gdsc_collections:{collection}"}
    else:
        return {"error": "Please provide either 'collection' or 'table_id'."}, 400

    documents, numresults = query_solr(f"{BASE_PATH}/dcat/select?wt=json&", query_parameters)
    if not documents:
        return {"error": "No documents found."}, 400

    # Generate output
    if fmt in ["bibtex", "ris"]:
        citations = [build_citation(doc, fmt) for doc in documents]
        output = ''.join(citations)
        filename = (name_id or collection or "citations") + f".{fmt}"
    else:
        return {"error": f"Unsupported format '{fmt}'."}, 400

    # Build response
    resp = make_response(output)
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    resp.headers["Content-Type"] = "text/plain"
    return resp

##
 # provide download api for derivate files
 ##
@app.route('/download/<path:download_path>', methods=["GET","POST"])
def download(download_path):

    if 'ImmutableMultiDict' in str(type(request.args)): args = request.args.to_dict()
    else: args = request.args

    # in case of reverse proxy
    download_path = download_path[download_path.index('data/'):]

    if 'format' in args:
        if args['format'] in ["sql","shp","geotiff","geojson"]:
            return send_from_directory(
                f"/{download_path}derived/",
                f"{args['file']}.{args['format']}.tar.gz",
                as_attachment=True
            )
        if args['format'] in ["json"]:
            return send_from_directory(
                f"/{download_path}derived/",
                f"{args['file']}.{args['format']}",
                as_attachment=True
            )

    return "File not found", 400


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
COLLECTIONS = dict(zip(keys, COLLECTIONS))
COLLECTIONS = OrderedDict(sorted(COLLECTIONS.items(), key=lambda i: i[0].lower()))


##
 # run the app if called from the command line
 ##

if __name__ == '__main__':
    # app.run(host='0.0.0.0')
    app.run(host='0.0.0.0',debug=True,use_reloader=True)
