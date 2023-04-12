import flask
from flask import request
from flask_cors import CORS
import config
from os.path import exists
import gen_example_data

app = flask.Flask(__name__)
CORS(app)

@app.route("/")
def main():
    return "I see you discovered our API 👀 why hello there"

# Register blueprints
from user import user
from auth import auth
from projects import projects
from moderation import mod
from notifications import notifs
from misc import misc

app.register_blueprint(user)
app.register_blueprint(auth)
app.register_blueprint(projects)
app.register_blueprint(mod)
app.register_blueprint(notifs)
app.register_blueprint(misc)

# Database things
if not exists(config.db):
    gen_example_data.reset()

# Run the app
if __name__ == "__main__":
    app.run(debug=True)