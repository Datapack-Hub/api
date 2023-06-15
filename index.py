import flask
from flask_cors import CORS

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
from routes.misc import misc

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


# Backups
# def backup():
#     put = requests.put(
#         "https://backups.datapackhub.net/" + date.today(),
#         open(config.DATA + "data.db", "rb"),
#         headers={
#             "Authorization": config.BACKUPS_TOKEN,
#         },
#         timeout=300,
#     )

#     if not put.ok:
#         print("It didn't work.")


# schedule.every().day.do(backup)

# while True:
#     schedule.run_pending()
#     time.sleep(1)

# Run the app
if __name__ == "__main__":
    debug_enabled = PROD == 1
    app.run(debug=debug_enabled)
