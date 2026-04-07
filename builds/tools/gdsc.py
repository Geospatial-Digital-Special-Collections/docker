from flask import Flask, render_template
import gdsc
from urllib.request import urlopen
from urllib.parse import urlencode
import simplejson
import logging
import json

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True


@app.route('/', methods=["GET"])
def index():
    """ render main page """

    # --- Render ---
    return render_template(
        "index.html"
    )

##
 # run the app if called from the command line
 ##

if __name__ == '__main__':
    # app.run(host='0.0.0.0')
    app.run(host='0.0.0.0',port=5150,debug=True,use_reloader=True)
