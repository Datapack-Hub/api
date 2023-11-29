from pathlib import Path

import flask
from flask_compress import Compress
from flask_cors import CORS
import waitress

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
CORS(app, supports_credentials=True)
Compress(app)


@app.route("/")
def main():
    return "I see you discovered our API 👀 why hello there"


@app.after_request
def after(response):
    response.headers["X-Robots-Tag"] = "noindex"
    return response


app.register_blueprint(user)
app.register_blueprint(auth)
app.register_blueprint(projects)
app.register_blueprint(versions)
app.register_blueprint(mod)
app.register_blueprint(notifs)
app.register_blueprint(comments)

# Database things
if not Path(config.DATA + "data.db").exists():
    gen_example_data.reset("no-drop")

# Run the app
if __name__ == "__main__":
    debug_enabled = PROD == 0
    if debug_enabled:
        app.run()
    else:
        waitress.serve(app)
