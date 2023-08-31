import json

from utilities import util
from utilities.commons import User


def from_username(self: str):
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where lower(username) = :uname",
        uname=self.lower(),
    ).one_or_none()

    if u is None:
        return None

    conn.close()

    badges = json.loads(u[5]) if u[5] else None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_id(self: int):
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where rowid = :id",
        id=self,
    ).one_or_none()

    if u is None:
        return None

    conn.close()

    badges = json.loads(u[5]) if u[5] else None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_github_id(self: int):
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where github_id = :id",
        id=self,
    ).one_or_none()

    if u is None:
        return None

    conn.close()

    badges = json.loads(u[5]) if u[5] else None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_discord_id(self: int):
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where discord_id = :id",
        id=self,
    ).one_or_none()

    if u is None:
        return None

    conn.close()

    badges = json.loads(u[5]) if u[5] else None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_token(token: str):
    conn = util.make_connection()

    # Select
    u = util.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where token = :token",
        token=token,
    ).one_or_none()

    if u is None:
        util.log("SillySilabearError: The user does not exist")
        return False

    conn.close()

    badges = json.loads(u[5]) if u[5] else None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)
