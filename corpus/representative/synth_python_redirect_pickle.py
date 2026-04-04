import pickle, base64
from flask import request, redirect

def handler():
    encoded = request.args["user"]
    user = pickle.loads(base64.b64decode(encoded))
    return redirect(request.args["next"])
