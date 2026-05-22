from flask import Flask, Response, render_template, request, send_from_directory, url_for, make_response
import gdsc
from urllib.request import urlopen
from urllib.parse import urlencode
import simplejson
import logging
import json

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True

# instantiate gdsc
auth = gdsc.authentication.Auth(env="local-k8s-flask")
pods = gdsc.pod.Pods(api=auth.api, pg=auth.pg)

# get metadata
meta = gdsc.metadata.Meta()

# finally the etl class
loader = gdsc.etl.Etl(
    api = auth.api,
    pg = auth.pg,
    meta = meta,
    pods = pods
)

# get the list of tables on disk
tables = meta.get_all_datasets_on_disk(pods)

@app.route('/', methods=["GET"])
def index():
    """ render main page """

    # --- Render ---
    return render_template(
        "index.html",
        pods = pods.pods, 
        tables = tables
    )

@app.route('/load/<dataset>', methods=["GET"])
def load(dataset):
    """ load a dataset """

    #dataset = request.args.get("dataset","")
    print(dataset)

    return {"name": dataset}


 # run the app if called from the command line


if __name__ == '__main__':
    # app.run(host='0.0.0.0')
    app.run(host='0.0.0.0',port=5150,debug=True,use_reloader=True)
