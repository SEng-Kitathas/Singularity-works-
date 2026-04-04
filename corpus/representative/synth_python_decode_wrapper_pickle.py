import pickle, base64
from flask import request
def safe_decode(x):
    return x
def load():
    blob = safe_decode(request.args["blob"])
    return pickle.loads(base64.b64decode(blob))
