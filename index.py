from pathlib import Path

import fastapi
import uvicorn

from fastapi.middleware import cors

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

app = fastapi.FastAPI()

origins = [
    "http://datapackhub.net",
    "https://files.datapackhub.net",
    "https://raw.files.datapackhub.net",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    cors.CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def main():
    return "I see you discovered our API 👀 why hello there"


def after(response):
    response.headers["X-Robots-Tag"] = "noindex"
    return response


app.include_router(user)
# app.register_blueprint(auth)
# app.register_blueprint(projects)
# app.register_blueprint(versions)
# app.register_blueprint(mod)
# app.register_blueprint(notifs)
# app.register_blueprint(comments)

# Database things
if not Path(config.DATA + "data.db").exists():
    gen_example_data.reset("no-drop")

# Run the app
if __name__ == "__main__":
    debug_enabled = PROD == 0
    uvicorn.run("index:app", reload=True)
    # app.run(debug=debug_enabled)
