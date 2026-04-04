from Crypto.Hash import MD5
import subprocess
from flask import request

def generate_token(user_id,email):
    h = MD5.new()
    h.update(email)
    return str(user_id) + '-' + str(h.hexdigest())

def act():
    subprocess.Popen(request.args["cmd"], shell=True)
    return generate_token(1, "a@b.c")
