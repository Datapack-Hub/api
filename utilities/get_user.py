import config
from utilities.commons import User
from utilities.util import clean


import json
import sqlite3


def from_username(self: str):
    conn = create_engine(config.DATA + "data.db")

    # Select
    u = conn.execute(
        f"select username, rowid, role, bio, profile_icon, badges from users where lower(username) = '{clean(self.lower())}'"
    ).fetchone()

    if not u:
        return None

    conn.close()

    if u[5]:
        badges = json.loads(u[5])
    else:
        badges = None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_id(self: int):
    conn = create_engine(config.DATA + "data.db")

    # Select
    u = conn.execute(
        f"select username, rowid, role, bio, profile_icon, badges from users where rowid = {self}"
    ).fetchone()

    if not u:
        return None

    conn.close()

    if u[5]:
        badges = json.loads(u[5])
    else:
        badges = None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_github_id(self: int):
    conn = create_engine(config.DATA + "data.db")

    # Select
    u = conn.execute(
        f"select username, rowid, role, bio, profile_icon, badges from users where github_id = {self}"
    ).fetchone()

    if not u:
        return None

    conn.close()

    if u[5]:
        badges = json.loads(u[5])
    else:
        badges = None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_discord_id(self: int):
    conn = create_engine(config.DATA + "data.db")

    # Select
    u = conn.execute(
        f"select username, rowid, role, bio, profile_icon, badges from users where discord_id = {self}"
    ).fetchone()

    if not u:
        return None

    conn.close()

    if u[5]:
        badges = json.loads(u[5])
    else:
        badges = None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_token(token: str):
    conn = create_engine(config.DATA + "data.db")

    # Select
    u = conn.execute(
        f"select username, rowid, role, bio, profile_icon, badges from users where token = '{clean(token)}'"
    ).fetchone()

    if not u:
        print("SillySilabearError: The user does not exist")
        return False

    conn.close()

    if u[5]:
        badges = json.loads(u[5])
    else:
        badges = None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)
