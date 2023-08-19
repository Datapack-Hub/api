import json

from utilities import util
from utilities.commons import User


def from_username(self: str):
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where lower(username) = :uname",
        uname=util.clean(self.lower()),
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
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where rowid = :id",
        id=self,
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
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where github_id = :id",
        id=self,
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
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where discord_id = :id",
        id=self,
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
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where token = :token",
        token=util.clean(token),
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
