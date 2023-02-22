import flask
from flask import request
import util

app = flask.Flask(__name__)

@app.route("/")
def main():
    return "I see you discovered our API 👀"

# Register blueprints
from user import user
from auth import auth
from projects import projects
from mctools import mctools

app.register_blueprint(user)
app.register_blueprint(auth)
app.register_blueprint(projects)
app.register_blueprint(mctools)

# Run the app
app.run()