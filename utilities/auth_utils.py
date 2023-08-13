import secrets
import config
from utilities.commons import User


import json
import sqlite3


def authenticate(auth: str):
    """
    `dict` - If success returns user details\n
    `31` - If auth not supplied\n
    `32` - If auth is not basic\n
    `33` - If user is not existing\n
    """
    if not auth:
        return 31
    if not auth.startswith("Basic"):
        return 32

    token = auth[6:]

    conn = create_engine(config.DATA + "data.db")

    u = conn.execute(
        f"select username, rowid, role, bio, profile_icon, badges from users where token = '{token}'"
    ).fetchone()
    if not u:
        print("user doth not exists")
        return 33
    conn.close()

    if u[5]:
        badges = json.loads(u[5])
    else:
        badges = None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def get_user_token(github_id: int):
    conn = create_engine(config.DATA + "data.db")

    # Select
    u = conn.execute(
        f"select token from users where github_id = {github_id}"
    ).fetchone()

    conn.close()

    if not u:
        return None

    return u[0]


def get_user_token_from_discord_id(discord: int):
    conn = create_engine(config.DATA + "data.db")

    # Select
    u = conn.execute(f"select token from users where discord_id = {discord}").fetchone()

    conn.close()

    if not u:
        return None

    return u[0]


def log_user_out(id: int):
    conn = create_engine(config.DATA + "data.db")

    token = secrets.token_urlsafe()

    # Create user entry in database
    try:
        conn.execute(f'UPDATE users SET token = "{token}" WHERE rowid = {id}')
    except sqlite3.Error as err:
        return err

    conn.commit()
    conn.close()

    return "Success!"
