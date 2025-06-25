from flask import Flask, render_template, request, send_from_directory, url_for
from urllib.request import urlopen
from urllib.parse import urlencode
import simplejson
import logging
import re
from collections import OrderedDict
from flask import Response
import io

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True

BASE_PATH = 'http://solr.gdsc:8983/solr/dcat/select?wt=json&'
SNIP_LENGTH = 180
QUERY_FIELDS = ['gdsc_collections','dct_title','dcat_keyword','dct_description','gdsc_attributes']

@app.route('/download_bibtex')
def download_bibtex():
    collection = request.args.get('collection', '*')
    query = request.args.get('query')
    active = request.args.get('active')

    q, qf = collection, "gdsc_collections "
    query_parameters = {"q": f"gdsc_collections:{collection}"}

    if query:
        qf += ' '.join(QUERY_FIELDS)
        q = f"{q} {query}".strip()

    if active:
        qf = f"{qf} gdsc_up"
        q = f"{q} true".strip()

    if qf.strip() != "gdsc_collections":
        query_parameters = {
            "q.op": "AND",
            "defType": "dismax",
            "qf": qf,
            "q": q
        }

    results, _ = query_solr(BASE_PATH, query_parameters)

    bibtex_entries = []
    for doc in results:
        entry = "@misc{"
        # Generate a simple key: FirstCreatorYearTitle (sanitized)
        key_parts = []
        if 'dct_creator' in doc:
            first_creator = doc['dct_creator'][0].split(';')[0].replace(' ', '')
            key_parts.append(first_creator)
        if 'dct_issued' in doc:
            key_parts.append(doc['dct_issued'][0][:4])
        if 'dct_title' in doc:
            key_parts.append(doc['dct_title'][0].split(' ')[0])

        bibkey = ''.join(key_parts) or 'citation'

        entry += f"{bibkey},\n"

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

        entry += "}\n\n"
        bibtex_entries.append(entry)

    bibtex_string = ''.join(bibtex_entries)
    return Response(
        bibtex_string,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=citations.bib"}
    )

def query_solr(path, parameters):
    numresults = 1
    results = []

    query_string = urlencode(parameters).replace('-', '+')
    while numresults > len(results):
        connection = urlopen(f"{path}{query_string}")
        response = simplejson.load(connection)
        numresults = response['response']['numFound']
        results = response['response']['docs']
        parameters["rows"] = numresults
        query_string = urlencode(parameters).replace('-', '+')
    if results is None:
        results = []

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

@app.route('/', methods=["GET", "POST"])
def index():
    collection = 'all'
    query, active = None, None
    query_parameters = {"q": "gdsc_collections:*"}
    q, qf = "", "gdsc_collections "
    numresults = 1
    results = []

    if request.method == "POST":
        if 'ImmutableMultiDict' in str(type(request.form)):
            args = request.form.to_dict()
        else:
            args = request.form
        if 'searchTerm' in args:
            query = re.sub(r'[\+\-\&\|\!\(\)\{\}\[\]\^\"\~\*\?\\:\\]', '', args["searchTerm"])
        if query in ("None", ""):
            query = None
        collection = args.get("collection", collection)
        if 'active' in args:
            active = args["active"] or None

        q = collection
        if collection in ('all', '*'):
            collection = '*'
            q = ""
        query_parameters = {"q": f"gdsc_collections:{collection}"}
        if query:
            qf += ' '.join(QUERY_FIELDS)
            q = f"{q} {query}".strip()
        if active:
            qf = f"{qf} gdsc_up"
            q = f"{q} true".strip()
        if qf.strip() != "gdsc_collections":
            query_parameters = {
                "q.op": "AND",
                "defType": "dismax",
                "qf": qf,
                "q": q
            }

    results, numresults = query_solr(BASE_PATH, query_parameters)

    for entry in results:
        if query:
            entry = highlight_query(entry, query)
        if entry.get('dct_description'):
            entry['display_description'] = entry['dct_description'][0]
            if len(entry['display_description']) > SNIP_LENGTH:
                entry['display_description'] = entry['dct_description'][0][:SNIP_LENGTH] + '...'

    if collection == "*":
        collection = 'all'

    return render_template(
        'index.html',
        collection=collection,
        query=query,
        active=active,
        numresults=numresults,
        results=results,
        collections=COLLECTIONS,
        switch_url=url_for('collections_view'),
        switch_label='Collections'
    )

@app.route('/detail/<name_id>', methods=["GET", "POST"])
def detail(name_id):
    args = request.args.to_dict()

    query_parameters = {"q": f"gdsc_tablename:{name_id}"}
    query_string = urlencode(query_parameters)
    connection = urlopen(f"{BASE_PATH}{query_string}")
    response = simplejson.load(connection)
    document = response['response']['docs'][0]

    if 'gdsc_attributes' in document:
        document['gdsc_columns'] = [attr.split(';')[0] for attr in document['gdsc_attributes']]

    if args.get('query'):
        document = highlight_query(document, args['query'])

    if 'gdsc_attributes' in document:
        document['gdsc_attributes'] = [attr.split(';') for attr in document['gdsc_attributes']]

    if 'gdsc_derivatives' in document:
        document['gdsc_derived'] = [attr.split(';') for attr in document['gdsc_derivatives']]

    return render_template('detail.html', name_id=name_id, document=document, referrer=request.args)

@app.route('/download/<path:download_path>', methods=["GET", "POST"])
def download(download_path):
    if 'ImmutableMultiDict' in str(type(request.args)):
        args = request.args.to_dict()
    else:
        args = request.args

    if 'format' in args and args['format'] in ("sql", "shp", "geotiff"):
        return send_from_directory(
            f"/{download_path}derived/",
            f"{args['file']}.{args['format']}.tar.gz",
            as_attachment=True
        )

    return "File not found", 400

# Get list of collections
COLLECTIONS, COLLECTIONS_COUNT = query_solr(
    'http://solr.gdsc:8983/solr/collections/select?wt=json&',
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

@app.route('/collections', methods=["GET", "POST"])
def collections_view():
    collection = list(COLLECTIONS.keys())[0]
    query, active = None, None
    query_parameters = {"q": "gdsc_collections:*"}
    q, qf = "", "gdsc_collections "
    numresults = 1
    results = []

    if request.method == "POST":
        if 'ImmutableMultiDict' in str(type(request.form)):
            args = request.form.to_dict()
        else:
            args = request.form
        if 'searchTerm' in args:
            query = re.sub(r'[\+\-\&\|\!\(\)\{\}\[\]\^\"\~\*\?\\:\\]', '', args["searchTerm"])
        if query in ("None", ""):
            query = None
        collection = args.get("collection", collection)
        if 'active' in args:
            active = args['active'] or None

        q = collection
        if collection in ('all', '*'):
            collection = '*'
            q = ""
        query_parameters = {"q": f"gdsc_collections:{collection}"}
        if query:
            qf += ' '.join(QUERY_FIELDS)
            q = f"{q} {query}".strip()
        if active:
            qf = f"{qf} gdsc_up"
            q = f"{q} true".strip()
        if qf.strip() != "gdsc_collections":
            query_parameters = {
                "q.op": "AND",
                "defType": "dismax",
                "qf": qf,
                "q": q
            }

    results, numresults = query_solr(BASE_PATH, query_parameters)

    for entry in results:
        if query:
            entry = highlight_query(entry, query)
        if entry.get('dct_description'):
            entry['display_description'] = entry['dct_description'][0]
            if len(entry['display_description']) > SNIP_LENGTH:
                entry['display_description'] = entry['dct_description'][0][:SNIP_LENGTH] + '...'

    if collection == "*":
        collection = 'all'

    return render_template(
        'collections.html',
        collection=collection,
        query=query,
        active=active,
        numresults=numresults,
        results=results,
        collections=COLLECTIONS,
        switch_url=url_for('index'),
        switch_label='Home'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, use_reloader=True)
