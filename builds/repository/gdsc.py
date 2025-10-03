from flask import Flask, Response, render_template, request, send_from_directory, url_for, make_response
from urllib.request import urlopen
from urllib.parse import urlencode
import simplejson
import logging
import re
from collections import OrderedDict
import io
from datetime import date

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True

BASE_PATH = 'http://gdsc-solr.gdsc:8983/solr/dcat/select?wt=json&'
SNIP_LENGTH = 180
QUERY_FIELDS = ['gdsc_collections','dct_title','dcat_keyword','dct_description','gdsc_attributes']
RESULTS_PER_PAGE = 10

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

@app.route('/cite', methods=["GET"])
def cite():
    # Extract URL arguments
    collection = request.args.get("collection", "all")
    name_id = request.args.get("name_id")
    fmt = request.args.get("format", "bibtex")    # default to bibtex

    # Build query parameters
    if name_id:
        query_parameters = {"q": f"gdsc_tablename:{name_id}"}
    elif collection:
        if collection == "all":
            query_parameters = {"q": "*:*"}
        else:
            query_parameters = {"q": f"gdsc_collections:{collection}"}
    else:
        return {"error": "Please provide either 'collection' or 'name_id'."}, 400

    documents, numresults = query_solr(BASE_PATH, query_parameters)

    if not documents:
        return {"error": "No documents found."}, 400

    # Generate citations
    if fmt in ["bibtex","ris"]:
        citations = [build_citation(doc, fmt) for doc in documents]
        output = ''.join(citations)
        filename = (name_id or collection or "citations") + f".{cite_formats['extension'][fmt]}"
        content_type = "text/plain"
    else:
        return {"error": f"Unsupported format '{fmt}'."}, 400

    # Build response
    resp = make_response(output)
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    resp.headers["Content-Type"] = content_type
    return resp

def build_citation(doc, type):
    """
    Returns a citation entry built from the doc in the given type
    """

    def build_element(field,value):
        return (
            f"{formatters['indent']}{field}{formatters['seperator']}"
            f"{formatters['quote_start']}{value}{formatters['quote_end']}"
            f"{formatters['line_seperator']}\n"
        )

    formatters = cite_formats['formatters'][type]
    entry = formatters['begin']
    if type == "bibtex":
        entry += f"{doc['gdsc_tablename'][0]}\n" or "citation\n"

    formatters = cite_formats['formatters'][type]
    # looped citation body construction
    for dc_term in cite_formats['fields']:
        field = cite_formats['fields'][dc_term]
        if type in field:
            if dc_term in doc:
                val = doc[dc_term]       
                if field['type'] in ["single", "date"]:
                    if dc_term in ["dct_issued"]: val[0] = val[0][:4]
                    if dc_term in ["dct_modified"]: val[0] = val[0].split('T')[0]    
                    entry += build_element(field[type],val[0])
                elif field['type'] == "list":
                    for item in val:
                        entry += build_element(field[type],item.split(";")[0])

    entry += formatters['end']
    return entry

def query_solr(path, parameters, start=0, end=None):
    results = []

    # Set 'start' and default 'rows' if not specified
    parameters["start"] = start
    parameters["rows"] = (end - start) if end is not None else parameters.get("rows", 10)

    query_string = urlencode(parameters).replace('-', '+')
    connection = urlopen(f"{path}{query_string}")
    response = simplejson.load(connection)
    
    numresults = response['response']['numFound']
    docs = response['response']['docs']
    
    results = docs if docs is not None else []

    return results, numresults

def highlight_query(document, query):
    """
    Returns a document with the query string highlighted for web page display
    """

    def add_tags(string_value, term):
        return re.sub(
            rf'({term})',
            '<span class="highlight-term">\\1</span>',
            string_value,
            flags=re.IGNORECASE
        )

    document['found_in'] = {}
    for field in QUERY_FIELDS:
        if field in document:
            attrs = []
            for i, attr in enumerate(document[field]):
                terms = query.split(' ')
                found = all(term.upper() in attr.upper() for term in terms)
                if found:
                    document['found_in'][field] = []
                    for term in terms:
                        document[field][i] = add_tags(document[field][i], term)
                    row = attr.split(';')
                    if len(row) > 1:
                        for j in range(2):
                            for term in terms:
                                row[j] = add_tags(row[j], term)
                        attrs.append([row[0], row[1]])
            if attrs:
                document['found_in'][field] = attrs

    return document

def search_solr(
    collection_arg="all",
    search_term=None,
    active=None,
    page=1,
    results_per_page=RESULTS_PER_PAGE
):
    """
    Shared Solr querying logic for / and /collections endpoints.
    Returns (results, numresults, collection, query).
    """

    collection = collection_arg or "all"
    query = None
    q, qf = collection, "gdsc_collections "

    # --- Clean query term ---
    if search_term:
        cleaned = re.sub(r'[\+\-\&\|\!\(\)\{\}\[\]\^\"\~\*\?\\:\\]', '', search_term)
        if cleaned not in ("None", ""):
            query = cleaned

    # --- Collection handling ---
    if collection in ("all", "*"):
        collection = "*"
        q = ""

    # --- Base query ---
    query_parameters = {"q": f"gdsc_collections:{collection}"}

    # --- Add search fields if query present ---
    if query:
        qf += " ".join(QUERY_FIELDS)
        q = f"{q} {query}".strip()

    # --- Add active filter if requested ---
    if active:
        qf = f"{qf} gdsc_up"
        q = f"{q} true".strip()

    # --- Switch to dismax only if needed ---
    if qf.strip() != "gdsc_collections":
        query_parameters = {
            "q.op": "AND",
            "defType": "dismax",
            "qf": qf,
            "q": q
        }

    # --- Query Solr ---
    start = (page - 1) * results_per_page
    end = page * results_per_page
    results, numresults = query_solr(BASE_PATH, query_parameters, start, end)

    # --- Post-process results ---
    for entry in results:
        if query:
            entry = highlight_query(entry, query)
        if entry.get("dct_description"):
            entry["display_description"] = entry["dct_description"][0]
            if len(entry["display_description"]) > SNIP_LENGTH:
                entry["display_description"] = entry["dct_description"][0][:SNIP_LENGTH] + "..."

    if collection == "*":
        collection = "all"

    return results, numresults, collection, query

@app.route('/', methods=["GET"])
def index():
    collection_arg = request.args.get("collection", "all")
    search_term_arg = request.args.get("searchTerm")
    active = request.args.get("active")

    results, numresults, collection, query = search_solr(
        collection_arg=collection_arg,
        search_term=search_term_arg,
        active=active,
        page=1  # index always shows page 1
    )

    return render_template(
        "index.html",
        collection=collection,
        query=query,
        active=active,
        numresults=numresults,
        results=results,
        collections=COLLECTIONS,
        collection_arg=collection_arg,
        search_term_arg=search_term_arg,
        switch_url="/collections",
        switch_label="Bibliography"
    )


@app.route('/collections', methods=["GET"])
def collections_view():
    page = int(request.args.get("page", 1))
    collection_arg = request.args.get("collection", "all")
    search_term_arg = request.args.get("searchTerm")
    active = request.args.get("active")

    results, numresults, collection, query = search_solr(
        collection_arg=collection_arg,
        search_term=search_term_arg,
        active=active,
        page=page
    )

    return render_template(
        "collections.html",
        collection=collection,
        query=query,
        active=active,
        numresults=numresults,
        results=results,
        collections=COLLECTIONS,
        switch_url=url_for("index"),
        switch_label="Standard",
        page=page,
        collection_arg=collection_arg,
        search_term_arg=search_term_arg
    )

@app.route('/detail/<name_id>', methods=["GET"])
def detail(name_id):
    args = request.args.to_dict()

    query_parameters = {"q": f"gdsc_tablename:{name_id}"}

    documents, numresults = query_solr(BASE_PATH, query_parameters)
    if not documents:
        return {"error": "No document found."}, 400
    document = documents[0]

    if 'gdsc_attributes' in document:
        document['gdsc_columns'] = [attr.split(';')[0] for attr in document['gdsc_attributes']]

    if args.get('query'):
        document = highlight_query(document, args['query'])

    if 'gdsc_attributes' in document:
        document['gdsc_attributes'] = [attr.split(';') for attr in document['gdsc_attributes']]

    if 'gdsc_derivatives' in document:
        document['gdsc_derived'] = [attr.split(';') for attr in document['gdsc_derivatives']]

    return render_template('detail.html', name_id=name_id, document=document, referrer=request.args)

@app.route('/download/<path:download_path>', methods=["GET"])
def download(download_path):
    args = request.args.to_dict()

    file_name = args.get("file")
    file_format = args.get("format")

    if file_name and file_format in ("sql", "shp", "geotiff"):
        return send_from_directory(
            f"/{download_path}derived/",
            f"{file_name}.{file_format}.tar.gz",
            as_attachment=True
        )

    return "File not found", 400

# Get list of collections
COLLECTIONS, COLLECTIONS_COUNT = query_solr(
    'http://gdsc-solr.gdsc:8983/solr/collections/select?wt=json&',
    {
        "q.op": "OR",
        "q": "Status:published"
    }
)

# 🔧 Ensure all items have a 'Creator' field
for item in COLLECTIONS:
    if 'Creator' not in item:
        item['Creator'] = [""]

keys = [item['Collection_ID'][0] for item in COLLECTIONS]
COLLECTIONS = dict(zip(keys, COLLECTIONS))
COLLECTIONS = OrderedDict(sorted(COLLECTIONS.items(), key=lambda i: i[0].lower()))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, use_reloader=True)
