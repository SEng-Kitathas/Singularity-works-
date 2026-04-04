from __future__ import unicode_literals

from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from app.models import User
from Crypto.Hash import MD5
import pickle
import base64


def generate_token(user_id, email):
    h = MD5.new()
    h.update(email)
    return str(user_id) + '-' + str(h.hexdigest())


@require_http_methods(["POST"])
def reset_password(request):
    if request.POST.get('user', '') != '':
        encoded_user = request.POST['user']
        user = pickle.loads(base64.b64decode(encoded_user))
        user.password = request.POST['password']
        user.save()
        messages.success(request, 'Your password has been updated')
    else:
        try:
            messages.error(request, 'Password did not reset')
        except:
            pass

    return redirect('/login')
