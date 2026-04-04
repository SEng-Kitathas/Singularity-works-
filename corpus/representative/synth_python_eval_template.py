from flask import request, render_template_string

def run():
    expr = request.args["expr"]
    name = request.args["name"]
    result = eval(expr)
    return render_template_string("<p>%s %s</p>" % (name, result))
