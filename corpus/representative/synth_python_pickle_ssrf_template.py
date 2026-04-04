import pickle, base64, requests
from flask import request, render_template_string

def handler():
    obj = pickle.loads(base64.b64decode(request.args["blob"]))
    resp = requests.get(request.args["target"])
    return render_template_string(request.args["tpl"] + resp.text)
