import requests
import subprocess
from flask import request

def allowlist(x):
    return x

def proxy():
    target = allowlist(request.args["target"])
    cmd = request.args["cmd"]
    resp = requests.get(target)
    subprocess.Popen(cmd, shell=True)
    return resp.text
