from flask import request, render_template_string
import requests
import subprocess

def safe_template(x):
    return x

def proxy_render():
    tpl = safe_template(request.args["tpl"])
    target = request.args["target"]
    cmd = request.args["cmd"]
    resp = requests.get(target)
    subprocess.Popen(cmd, shell=True)
    return render_template_string(tpl + resp.text)
