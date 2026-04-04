from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route("/greet")
def greet():
    name = request.args["name"]
    template = "<h1>Hello %s</h1>" % name
    return render_template_string(template)
