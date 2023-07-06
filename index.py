from os.path import exists

import flask
from flask_compress import Compress
from flask_cors import CORS

import config
import gen_example_data
from prod import PROD

# Register blueprints
from routes.auth import auth
from routes.comments import comments
from routes.moderation import mod
from routes.notifications import notifs
from routes.projects import projects
from routes.user import user
from routes.versions import versions

app = flask.Flask(__name__)
CORS(app)
Compress(app)


@app.route("/")
def main():
    return "I see you discovered our API 👀 why hello there"


@app.after_request
def after(resp):
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


app.register_blueprint(user)
app.register_blueprint(auth)
app.register_blueprint(projects)
app.register_blueprint(versions)
app.register_blueprint(mod)
app.register_blueprint(notifs)
app.register_blueprint(comments)

# Database things
if not exists(config.DATA + "data.db"):
    gen_example_data.reset()

# Run the app
if __name__ == "__main__":
    debug_enabled = PROD == 1
    app.run(debug=debug_enabled)
