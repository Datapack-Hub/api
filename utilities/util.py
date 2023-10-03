import logging
import random
import secrets
import time
from functools import lru_cache

from sqlalchemy import Connection, CursorResult, Engine, create_engine, text

import config
from utilities import post


def make_connection() -> Connection:
    return create_engine("sqlite:///" + config.DATA + "data.db").connect()


def exec_query(conn: Connection, query: str, **params) -> CursorResult:
    q = text(query)

    if params:
        q = q.bindparams(**params)
    return conn.execute(q)


def commit_query(command: str, **params) -> CursorResult:
    conn = make_connection()
    q = text(command)

    if params:
        q = q.bindparams(**params)
    result = conn.execute(q)
    conn.commit()
    conn.close()
    return result


def log(msg: object, level=logging.INFO):
    logging.basicConfig(level=level, format=config.PYTHON_LOGGING_CONF)
    logging.log(level=level, msg=msg)


def create_user_account(
    github_data: dict,
):
    conn = make_connection()

    token = secrets.token_urlsafe()

    check = exec_query(
        conn,
        "select username from users where username = :login;",
        login=github_data["login"],
    ).all()
    if not check:
        username = github_data["login"]
    else:
        username = github_data["login"] + str(random.randint(1, 99999))

    # Create user entry in database
    exec_query(
        conn,
        'INSERT INTO users (username, role, bio, github_id, token, profile_icon, join_date) VALUES (:g_login, "default", "A new Datapack Hub user!", :id, :token, :avatar, :join)',
        g_login=username,
        id=github_data["id"],
        token=token,
        avatar=github_data["avatar_url"],
        join=time.time(),
    )

    conn.commit()
    conn.close()

    log("CREATED USER: " + github_data["login"])

    return token


@lru_cache
def get_user_ban_data(id: int):
    conn = make_connection()

    banned_user = exec_query(
        conn,
        "select reason, expires from banned_users where id = :id",
        id=id,
    ).one_or_none()

    conn.close()

    if banned_user is None:
        return None

    return {"reason": banned_user[0], "expires": banned_user[1]}


@lru_cache
def user_owns_project(project: int, author: int):
    conn = make_connection()
    proj = exec_query(
        conn,
        "select rowid from projects where rowid = :project and author = :author",
        project=project,
        author=author,
    ).all()
    conn.close()
    return len(proj) == 1


# def get_user_data(id: int, data: list[str])
#     ).one()


def send_notif(conn: Engine, title: str, msg: str, receiver: int):
    exec_query(
        conn,
        "INSERT INTO notifs VALUES (:title, :msg, False, 'default', :uid})",
        title=title,
        msg=msg,
        uid=receiver,
    )


# Define a custom sorting key function
def custom_sort_key(version):
    # Split the version string by '.' into a list of components
    components = version.split(".")

    # Replace 'x' with a large number for sorting
    for i in range(len(components)):
        if components[i] == "x":
            components[i] = "999999"

    # Convert components to integers for sorting
    return [int(component) for component in components]


if __name__ == "__main__":
    post.approval(
        "Silabear",
        "Hexenwerk",
        "Magic datapack which adds wands, spells, etc. and will soon even be well polished!",
        "https://files.datapackhub.net/icons/174209.png",
        "Flynecraft",
    )
