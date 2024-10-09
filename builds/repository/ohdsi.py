from flask import Flask, render_template, request
from urllib.request import urlopen
from urllib.parse import urlencode
import simplejson
import logging
import re

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True

BASE_PATH='http://gaia-solr:8983/solr/dcat/select?wt=json&'
SNIP_LENGTH = 180
QUERY_FIELDS = ['dct_title','dct_keywords','dct_description','gdsc_attributes']

##
 # highlight found instances of query in document metadata
 ##
def highlight_query(document,query):

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
                    print(field)
                    for term in terms:
                        print(term)
                        document[field][i] = add_tags(document[field][i],term)
                    print(document[field][i])
                    row = attr.split(';')
                    if len(row) > 1:
                        print (row[0])
                        document[field][i] = add_tags(document[field][i],row[0]) 
                        print(document[field][i])
                        for j in range(0,2):
                            for term in terms:
                                row[j] = add_tags(row[j],term)
                        print(row[0])
                        row[0] = add_tags(row[0],row[0])
                        print(row[0]) 
                        attrs.append([row[0],row[1]])
                        print(attrs)
            if len(attrs) > 0: document['found_in'][field] = attrs

    return document

##
 # run SOLR query and render results for main page
 ##
@app.route('/', methods=["GET","POST"])
def index():
    query, active = None, None
    query_parameters = {"q": "*:*"}
    q, qf = "*:*", ""
    numresults = 1
    results = []

    # get the search term if entered, and attempt
    # to gather results to be displayed
    if request.method == "POST":
        query = request.form["searchTerm"]
        if 'active' in request.form:
            active = request.form["active"]

        #print ('query:', query)
        #print ('active:', active)

        q = "*;*"
        query_parameters = {"q": "*:*"}
        if query is not None and query != "":
            qf += "dct_title dct_keywords dct_description gdsc_attributes"
            if len(q) > 0: q += " "
            q += query
        if active is not None:
            if qf != "gdsc_collections ": qf += " "
            qf += "gdsc_up"
            if len(q) > 0: q += " "
            q += "true"
        if qf != "":
            query_parameters = {
              "q.op": "AND",
              "defType": "dismax",
              "qf": qf,
              "q": q
            }

    # query for information and return results
    query_string  = urlencode(query_parameters)
    print(query_string)
    while numresults > len(results): 
        connection = urlopen("{}{}".format(BASE_PATH, query_string))
        response = simplejson.load(connection)
        numresults = response['response']['numFound']
        results = response['response']['docs']
        query_parameters["rows"] = numresults
        query_string  = urlencode(query_parameters) 
        #print('loop:',query_string) 
    
    if results == None: results=[]

    # check results for correct display
    for entry in results:

        # highlight search term in results
        if query != None and query != 'None' and query != '':
            entry = highlight_query(entry,query)

        # snip abstracts
        if entry['dct_description']:
            entry['display_description'] = entry['dct_description'][0]
            if len(entry['display_description']) > SNIP_LENGTH:
                entry['display_description'] = entry['dct_description'][0][0:SNIP_LENGTH] + '...'

    return render_template('index.html',  query=query, active=active, numresults=numresults, results=results)

##
 # query SOLR for one document and render all metadata in detail
 ##
@app.route('/detail/<name_id>', methods=["GET","POST"])
def detail(name_id):

    args = request.args.to_dict() 

    query_parameters = {"q": "gdsc_tablename:" + name_id}
    query_string  = urlencode(query_parameters)
    print(query_string)
    connection = urlopen("{}{}".format(BASE_PATH, query_string))
    response = simplejson.load(connection)
    document = response['response']['docs'][0]

    if 'gdsc_attributes' in document:                                                             
        document['gdsc_columns'] = [attr.split(';')[0] for attr in document['gdsc_attributes']]

    if args['query'] != None and args['query'] != 'None' and args['query'] != '':
        document = highlight_query(document,args['query'])

    if 'gdsc_attributes' in document: 
        document['gdsc_attributes'] = [attr.split(';') for attr in document['gdsc_attributes']]   

    return render_template('detail.html', name_id=name_id, document=document, referrer=request.args)

##
 # load variable
 ##
@app.route('/load/<variable_id>', methods=["GET","POST"])
def load(variable_id):

    query_parameters = {"variable_id": variable_id}
    query_string  = urlencode(query_parameters) 
    connection = urlopen("http://gaia-core:8000/load?{}".format(query_string))                                             
    response = simplejson.load(connection)

    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True,use_reloader=True,port=5000)/ohdsi