from flask import Flask, render_template, request, send_from_directory, url_for
from urllib.request import urlopen
from urllib.parse import urlencode
import simplejson
import logging
import re
from collections import OrderedDict
from flask import Response
import io
from flask import make_response
from datetime import date

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True

BASE_PATH = 'http://gdsc-solr.gdsc:8983/solr/dcat/select?wt=json&'
SNIP_LENGTH = 180
QUERY_FIELDS = ['gdsc_collections','dct_title','dcat_keyword','dct_description','gdsc_attributes']
RESULTS_PER_PAGE = 10


bibtex = {
    "author": {
        "type": "list",
        "key": "dct_creator"
    },
    "year": {
        "type": "year",
        "key": "dct_issued"
    },
    "title": {
        "type": "single",
        "key": "dct_title"
    },
    "publisher": {
        "type": "single",
        "key": "dct_publisher"
    },
    "url": {
        "type": "single",
        "key": "dct_identifier"
    },
    "keywords": {
        "type": "list",
        "key": "dcat_keyword"
    },
    "timestamp": {
        "type": "single",
        "key": "dct_modified"
    },
    "language": {
        "type": "single",
        "key": "dct_language"
    },
    "annote": {
        "type": "single",
        "key": "dct_description"
    }

}


ris = {
    "AU": {
        "type": "list",
        "key": "dct_creator"
    },
    "PY": {
        "type": "year",
        "key": "dct_issued"
    },
    "TI": {
        "type": "single",
        "key": "dct_title"
    },
    "PB": {
        "type": "single",
        "key": "dct_publisher"
    },
    "UR": {
        "type": "single",
        "key": "dct_identifier"
    },
    "KW": {
        "type": "list",
        "key": "dcat_keyword"
    },
    "Y2": {
        "type": "single",
        "key": "dct_modified"
    },
    "LA": {
        "type": "single",
        "key": "dct_language"
    },
    "AB": {
        "type": "single",
        "key": "dct_description"
    },
    "WV": {
        "type": "single",
        "key": "gdsc_version"
    },
    "T3": {
        "type": "single",
        "key": "gdsc_collections"
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
    if fmt == "bibtex":
        citations = [construct_bibtex_entry(doc) for doc in documents]
        output = ''.join(citations)
        filename = (name_id or collection or "citations") + ".bib"
        content_type = "text/plain"
    elif fmt == "ris":
        citations = [construct_ris_entry(doc) for doc in documents]
        output = ''.join(citations)
        filename = (name_id or collection or "citations") + ".ris"
        content_type = "text/plain"
    else:
        return {"error": f"Unsupported format '{fmt}'."}, 400

    # Build response
    resp = make_response(output)
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    resp.headers["Content-Type"] = content_type
    return resp


def construct_bibtex_entry(doc):
    entry = "@misc{"
    key_parts = []

    if 'gdsc_tablename' in doc:
        first_creator = doc['gdsc_tablename'][0]
        key_parts.append(first_creator)

    bibkey = ''.join(key_parts) or 'citation'
    entry += bibkey + ",\n"

    # date of resource access
    entry += f"  urldate = {{{date.today().isoformat()}}},\n"

    if 'dct_creator' in doc:
        creators = ' and '.join([c.split(';')[0] for c in doc['dct_creator']])
        entry += f"  author = {{{creators}}},\n"
    if 'dct_issued' in doc:
        entry += f"  year = {{{doc['dct_issued'][0][:4]}}},\n"
    if 'dct_title' in doc:
        entry += f"  title = {{{doc['dct_title'][0]}}},\n"
    if 'dct_publisher' in doc:
        entry += f"  publisher = {{{doc['dct_publisher'][0]}}},\n"
    if 'dct_identifier' in doc:
        entry += f"  url = {{{doc['dct_identifier'][0]}}},\n"
    if 'dcat_keyword' in doc:
        keywords = ', '.join([c.split(';')[0] for c in doc['dcat_keyword']])
        entry += f"  keywords = {{{keywords}}},\n"
    if 'dct_modified' in doc:
        timestamp = (doc['dct_modified'][0]).split('T')[0]
        entry += f"  timestamp = {{{timestamp}}},\n"
    if 'dct_language' in doc:
        entry += f"  language = {{{doc['dct_language'][0]}}},\n"
    if 'dct_description' in doc:
        entry += f"  annote = {{{doc['dct_description'][0]}}},\n"


    entry += "}\n\n"
    return entry


def construct_ris_entry(doc):
    entry = "TY  - DATA\n"

    # date of resource access
    entry += f"Y3  - {date.today().isoformat()}\n"

    if 'dct_creator' in doc:
        creators = [c.split(';')[0] for c in doc['dct_creator']]
        for creator in creators:
            entry += f"AU  - {creator}\n"
    if 'dct_issued' in doc:
        year = doc['dct_issued'][0][:4]
        entry += f"PY  - {year}\n"
    if 'dct_title' in doc:
        entry += f"TI  - {doc['dct_title'][0]}\n"
    if 'dct_publisher' in doc:
        entry += f"PB  - {doc['dct_publisher'][0]}\n"
    if 'dct_identifier' in doc:
        entry += f"UR  - {doc['dct_identifier'][0]}\n"
    if 'dcat_keyword' in doc:
        keywords = [k.split(';')[0] for k in doc['dcat_keyword']]
        for keyword in keywords:
            entry += f"KW  - {keyword}\n"
    if 'dct_modified' in doc:
        timestamp = doc['dct_modified'][0].split('T')[0]
        entry += f"Y2  - {timestamp}\n"
    if 'dct_language' in doc:
        entry += f"LA  - {doc['dct_language'][0]}\n"
    if 'dct_description' in doc:
        entry += f"AB  - {doc['dct_description'][0]}\n"
    if 'gdsc_version' in doc:
        entry += f"WV  - {doc['gdsc_version'][0]}\n"
    if 'gdsc_collections' in doc:
        entry += f"T3  - {doc['gdsc_collections'][0]}\n"

    entry += "ER  - \n\n"

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
