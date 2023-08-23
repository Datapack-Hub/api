import json
import secrets
import sqlite3

from utilities import util
from utilities.commons import User


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

    conn = util.make_connection()

    u = util.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where token = :token",
        token=token,
    ).one()
    if not u:
        print("user doth not exists")
        return 33
    conn.close()

    badges = json.loads(u[5]) if u[5] else None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def get_user_token(github_id: int):
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn, "select token from users where github_id = :g_id", g_id=github_id
    ).one()

    conn.close()

    if not u:
        return None

    return u[0]


def get_user_token_from_discord_id(discord: int):
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn, "select token from users where discord_id = :discord", discord=discord
    ).one()

    conn.close()

    if not u:
        return None

    return u[0]


def log_user_out(id: int):
    conn = util.make_connection()

    token = secrets.token_urlsafe()

    # Create user entry in database
    try:
        util.exec_query(
            conn,
            "UPDATE users SET token = :token WHERE rowid = :id",
            token=token,
            id=id,
        )
    except sqlite3.Error as err:
        return err

    conn.commit()
    conn.close()

    return "Success!"
