import flask
from flask_cors import CORS
from flask_compress import Compress

import config
from os.path import exists
import gen_example_data
from prod import PROD

# Register blueprints
from routes.user import user
from routes.auth import auth
from routes.projects import projects
from routes.versions import versions
from routes.moderation import mod
from routes.notifications import notifs
from routes.comments import comments
from routes.misc import misc

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
app.register_blueprint(misc)

# Database things
if not exists(config.DATA + "data.db"):
    gen_example_data.reset()

# Run the app
if __name__ == "__main__":
    debug_enabled = PROD == 1
    app.run(debug=debug_enabled)
