from flask import request, render_template_string
def greet():
    tpl = "<h1>Hello %s</h1>" % request.args["name"]
    return render_template_string(tpl)
