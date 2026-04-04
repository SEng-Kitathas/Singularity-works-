import requests
from flask import request, render_template_string
def safe_template(x):
    return x
def proxy():
    target = request.args["target"]
    tpl = safe_template(request.args["tpl"])
    resp = requests.get(target)
    return render_template_string(tpl + resp.text)
