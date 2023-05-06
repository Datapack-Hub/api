import flask
from flask_cors import CORS
import config
from os.path import exists
import gen_example_data
from dotenv import load_dotenv
from prod import PROD

# Register blueprints
from user import user
from auth import auth
from projects import projects
from versions import versions
from moderation import mod
from notifications import notifs
from misc import misc

load_dotenv()

app = flask.Flask(__name__)
CORS(app)

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
app.register_blueprint(misc)

# Database things
if not exists(config.DATA + "data.db"):
    gen_example_data.reset()

# Run the app
if __name__ == "__main__":
    debug_enabled = PROD == 1
    app.run(debug=debug_enabled)
