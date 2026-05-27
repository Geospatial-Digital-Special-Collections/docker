from flask import Flask, Response, render_template, request, send_from_directory, make_response
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
 # Globals
 ##

BASE_PATH = 'http://gdsc-solr.gdsc:8983/solr'
SNIP_LENGTH = 180
QUERY_FIELDS = ['gdsc_collections', 'dct_title', 'dcat_keyword', 'dct_description', 'gdsc_attributes']
DEFAULT_ROWS = 10
DEBUG = True

FILTER_SPECS = {
    "collections": {
        "field": "gdsc_collections_str",
        "facet_name": "possible_collections",
        "frontend_name": "Collections"
    },
    "keyword": {
        "field": "dcat_keyword_str",
        "facet_name": "possible_keywords",
        "frontend_name": "Keywords"
    },
    "geometry": {
        "field": "locn_geometry_str",
        "facet_name": "possible_geometries",
        "frontend_name": "Geometry"
    },
    "representation": {
        "field": "adms_representationTechnique_str",
        "facet_name": "possible_representations",
        "frontend_name": "Representation"
    },
    "right": {
        "field": "dct_rights_str",
        "facet_name": "possible_rights",
        "frontend_name": "Rights"
    },
    "active": {
        "field": "gdsc_up",
        "facet_name": "possible_activity",
        "frontend_name": "Running"
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
    :param facet_field: optional field for facet counts; if unspecified, queries normally
    :return: the query results, the number of results
    :rtype: tuple
    """
    query_string = urlencode(parameters)
    url = f"{path}{query_string}"

    try:
        with urlopen(url) as connection:
            response = simplejson.load(connection)
    except Exception as e:
        print(f"Error querying SOLR: {e}")
        return [], 0

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


def highlight_query(document: dict, query: str) -> dict:
    """
    Highlight the query text in the given document.

    :param dict document: the document metadata
    :param str query: string to highlight in the document
    :return: the document metadata with CSS highlight spans added to matching fields
    :rtype: dict
    """
    def add_tags(string_value, term):
        return re.sub(
            r'(' + re.escape(term) + ')',
            r'<span class="highlight-term">\1</span>',
            string_value,
            flags=re.IGNORECASE
        )

    document['found_in'] = {}
    terms = query.split(' ')

    for field in QUERY_FIELDS:
        if field not in document:
            continue
        attrs = []
        for i, attr in enumerate(document[field]):
            if not all(term.upper() in attr.upper() for term in terms):
                continue
            document['found_in'][field] = []
            for term in terms:
                document[field][i] = add_tags(document[field][i], term)
            row = attr.split(';')
            if len(row) > 1:
                document[field][i] = add_tags(document[field][i], row[0])
                for j in range(2):
                    for term in terms:
                        row[j] = add_tags(row[j], term)
                row[0] = add_tags(row[0], row[0])
                attrs.append([row[0], row[1]])
        if attrs:
            document['found_in'][field] = attrs

    return document


def build_citation(document: dict, fmt: str) -> str:
    """
    Create a formatted citation string for the document.

    :param dict document: the document metadata
    :param str fmt: the format type, one of "bibtex" or "ris"
    :return: the formatted citation
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
        "fields": {
            "dct_creator":    {"type": "list",   "bibtex": "author",    "ris": "AU"},
            "dct_issued":     {"type": "date",   "bibtex": "year",      "ris": "PY"},
            "dct_title":      {"type": "single", "bibtex": "title",     "ris": "TI"},
            "dct_publisher":  {"type": "single", "bibtex": "publisher", "ris": "PB"},
            "dct_identifier": {"type": "single", "bibtex": "url",       "ris": "UR"},
            "dcat_keyword":   {"type": "list",   "bibtex": "keywords",  "ris": "KW"},
            "dct_modified":   {"type": "date",   "bibtex": "timestamp", "ris": "Y2"},
            "dct_language":   {"type": "single", "bibtex": "language",  "ris": "LA"},
            "gdsc_version":   {"type": "single", "ris": "WV"},
            "gdsc_collections": {"type": "single", "ris": "T3"}
        }
    }

    formatters = cite_formats['formatters'][fmt]

    def build_element(field, value):
        return (
            f"{formatters['indent']}{field}{formatters['seperator']}"
            f"{formatters['quote_start']}{value}{formatters['quote_end']}"
            f"{formatters['line_seperator']}\n"
        )

    entry = formatters['begin']
    if fmt == "bibtex":
        entry += f"{document.get('gdsc_tablename', ['citation'])[0]}\n"

    for dc_term, field in cite_formats['fields'].items():
        if fmt not in field or dc_term not in document:
            continue
        val = list(document[dc_term])  # copy to avoid mutating the document
        if field['type'] in ("single", "date"):
            if dc_term == "dct_issued":
                val[0] = val[0][:4]
            elif dc_term == "dct_modified":
                val[0] = val[0].split('T')[0]
            entry += build_element(field[fmt], val[0])
        elif field['type'] == "list":
            for item in val:
                entry += build_element(field[fmt], item.split(";")[0])

    entry += formatters['end']
    return entry


def fetch_facets(field: str, query: str, fq: str) -> tuple:
    """
    Fetch facet counts from SOLR for a given field.

    :param str field: the Solr field to facet on
    :param str query: the current search query
    :param str fq: the current filter query string
    :return: the facet values and count
    :rtype: tuple
    """
    params = {
        "q": query,
        "q.op": "AND",
        "fq": fq,
        "defType": "edismax",
        "qf": ' '.join(QUERY_FIELDS),
        "facet.field": field,
        "indent": "true",
        "rows": "0",
        "facet": "true",
        "facet.mincount": "1",
        "facet.limit": "-1",
        "facet.sort": "count"
    }
    return query_solr(f'{BASE_PATH}/dcat/select?wt=json&', params, field)


##
 # Routes and views
 ##

@app.route('/', methods=["GET"])
def index() -> str:
    """
    Render HTML for the top-level route of the application.

    :return: HTML for the index page
    :rtype: str
    """
    collection = request.args.get("collection", "all")
    query = request.args.get("query", "")
    page = int(request.args.get("page", 1))

    selected_filters = {key: request.args.getlist(key) for key in FILTER_SPECS}

    q = query or "*"

    fq_parts = ["gdsc_collections:*" if collection == "all" else f'gdsc_collections:"{collection}"']

    for key, values in selected_filters.items():
        if values:
            field = FILTER_SPECS[key]["field"]
            clauses = [f'{field}:"{v}"' for v in values]
            fq_parts.append(f"({' AND '.join(clauses)})")

    fq = " ".join(fq_parts)

    query_parameters = {
        "q.op": "AND",
        "defType": "edismax",
        "fq": fq,
        "q": q,
        "qf": ' '.join(QUERY_FIELDS),
        "start": (page - 1) * DEFAULT_ROWS,
        "rows": DEFAULT_ROWS
    }

    results, numresults = query_solr(f'{BASE_PATH}/dcat/select?wt=json&', query_parameters)

    for entry in results:
        if query:
            highlight_query(entry, query)
        if entry.get('dct_description'):
            desc = entry['dct_description'][0]
            entry['display_description'] = desc[:SNIP_LENGTH] + '...' if len(desc) > SNIP_LENGTH else desc

    if collection == "*":
        collection = "all"

    facet_data = {}
    for key, spec in FILTER_SPECS.items():
        values, _ = fetch_facets(spec["field"], q, fq)
        if key == "collections":
            facet_data[spec["facet_name"]] = [
                y for i in range(0, len(values) // 2)
                if values[i * 2] in COLLECTIONS
                for y in (values[i * 2], values[i * 2 + 1])
            ]
        else:
            facet_data[spec["facet_name"]] = values

    return render_template(
        "index.html",
        collection=collection,
        query=query,
        page=page,
        results=results,
        numresults=numresults,
        collections=COLLECTIONS,
        filter_specs=FILTER_SPECS,
        root="./",
        facet_data=facet_data,
        selected_filters=selected_filters
    )


@app.route('/detail/<name_id>', methods=["GET", "POST"])
def detail(name_id: str) -> str:
    """
    Query SOLR for one document and render its metadata detail page.

    :param str name_id: the unique identifier for the dataset (tablename)
    :return: HTML for the detail page
    :rtype: str
    """
    args = request.args.to_dict()

    query_parameters = {"q": f"gdsc_tablename:{name_id}"}
    query_string = urlencode(query_parameters)
    connection = urlopen(f'{BASE_PATH}/dcat/select?wt=json&{query_string}')
    response = simplejson.load(connection)
    document = response['response']['docs'][0]

    query_arg = args.get('query')
    if query_arg:
        highlight_query(document, query_arg)
    args['query'] = query_arg or None

    if 'gdsc_attributes' in document:
        document['gdsc_columns'] = [attr.split(';')[0] for attr in document['gdsc_attributes']]
        document['gdsc_attributes'] = [attr.split(';') for attr in document['gdsc_attributes']]

    # BUG FIX: was checking gdsc_derivatives but splitting gdsc_derived
    if 'gdsc_derivatives' in document:
        document['gdsc_derivatives'] = [attr.split(';') for attr in document['gdsc_derivatives']]

    try:
        with open(f"/data/{name_id}/meta_json-ld_{name_id}.json", 'r', encoding='utf-8') as f:
            json_ld = json.load(f)
    except Exception:
        json_ld = ""

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
def cite(fmt: str, collection: str = None, table_id: str = None) -> Response:
    """
    Create formatted citations and return as a download Response.

    :param str collection: the unique identifier for the collection
    :param str table_id: the unique identifier for the dataset (tablename)
    :param str fmt: the citation format, one of "bibtex" or "ris"
    :return: formatted citations as a Flask Response
    :rtype: Response
    """
    if table_id:
        query_parameters = {"q": f"gdsc_tablename:{table_id}"}
        label = table_id
    elif collection:
        query_parameters = {"q": "*:*" if collection == "all" else f"gdsc_collections:{collection}"}
        label = collection
    else:
        return {"error": "Please provide either 'collection' or 'table_id'."}, 400

    documents, _ = query_solr(f"{BASE_PATH}/dcat/select?wt=json&", query_parameters)
    if not documents:
        return {"error": "No documents found."}, 400

    if fmt not in ("bibtex", "ris"):
        return {"error": f"Unsupported format '{fmt}'."}, 400

    output = ''.join(build_citation(doc, fmt) for doc in documents)
    extension = "bib" if fmt == "bibtex" else fmt
    filename = f"{label}.{extension}"

    resp = make_response(output)
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    resp.headers["Content-Type"] = "text/plain"
    return resp


@app.route('/download/<path:download_path>', methods=["GET", "POST"])
def download(download_path: str) -> Response:
    """
    Retrieve the correct derivative for download and return as a Flask Response.

    :param str download_path: the path to the derivative for download
    :return: the derivative package as a Flask Response
    :rtype: Response
    """
    args = request.args.to_dict()

    # BUG FIX: guard against ValueError if 'data/' is not in the path
    if 'data/' in download_path:
        download_path = download_path[download_path.index('data/'):]
    else:
        return "Invalid download path", 400

    fmt = args.get('format')
    file = args.get('file')

    if fmt in ("sql", "shp", "geotiff", "geojson"):
        return send_from_directory(f"/{download_path}derived/", f"{file}.{fmt}.tar.gz", as_attachment=True)
    if fmt == "json":
        return send_from_directory(f"/{download_path}derived/", f"{file}.{fmt}", as_attachment=True)

    return "File not found", 400


##
 # Always fetch the list of collections on startup
 ##

COLLECTIONS, COLLECTIONS_COUNT = query_solr(
    f'{BASE_PATH}/collections/select?wt=json&',
    {"q.op": "OR", "q": "Status:published"}
)
keys = [item['CollectionID'][0] for item in COLLECTIONS]
COLLECTIONS = OrderedDict(sorted(dict(zip(keys, COLLECTIONS)).items(), key=lambda i: i[0].lower()))


##
 # Run the app if called from the command line
 ##

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, use_reloader=True)
