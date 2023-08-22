import json

from utilities.commons import User
import utilities.db


def from_username(self: str):
    conn = utilities.db.make_connection()

    # Select
    u = utilities.db.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where lower(username) = :uname",
        uname=self.lower(),
    ).fetchone()

    if not u:
        return None

    conn.close()

    badges = json.loads(u[5]) if u[5] else None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_id(self: int):
    conn = utilities.db.make_connection()

    # Select
    u = utilities.db.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where rowid = :id",
        id=self,
    ).fetchone()

    if not u:
        return None

    conn.close()

    badges = json.loads(u[5]) if u[5] else None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_github_id(self: int):
    conn = utilities.db.make_connection()

    # Select
    u = utilities.db.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where github_id = :id",
        id=self,
    ).fetchone()

    if not u:
        return None

    conn.close()

    badges = json.loads(u[5]) if u[5] else None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_discord_id(self: int):
    conn = utilities.db.make_connection()

    # Select
    u = utilities.db.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where discord_id = :id",
        id=self,
    ).fetchone()

    if not u:
        return None

    conn.close()

    badges = json.loads(u[5]) if u[5] else None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)


def from_token(token: str):
    conn = utilities.db.make_connection()

    # Select
    u = utilities.db.exec_query(
        conn,
        "select username, rowid, role, bio, profile_icon, badges from users where token = :token",
        token=token,
    ).fetchone()

    if not u:
        print("SillySilabearError: The user does not exist")
        return False

    conn.close()

    badges = json.loads(u[5]) if u[5] else None
    return User(u[1], u[0], u[2], u[3], profile_icon=u[4], badges=badges)
