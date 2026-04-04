import base64
import pickle
from django.shortcuts import redirect

def reset_password(request):
    if request.POST.get('user', '') != '':
        encoded_user = request.POST['user']
        user = pickle.loads(base64.b64decode(encoded_user))

        user.password = request.POST['password']
        user.save()
    return redirect('/login')
