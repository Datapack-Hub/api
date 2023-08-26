import random
import secrets
from functools import lru_cache

from sqlalchemy import Connection, CursorResult, Engine, create_engine, text

import config
from utilities import post
from utilities.commons import ShortBanData


def make_connection() -> Connection:
    return create_engine("sqlite:///" + config.DATA + "data.db").connect()


def exec_query(conn: Connection, query: str, **params) -> CursorResult:
    q = text(query)

    if params:
        q = q.bindparams(**params)
    return conn.execute(q)


def create_user_account(github_data: dict) -> str:
    conn = make_connection()

    token = secrets.token_urlsafe()

    check = exec_query(
        conn,
        "select username from users where username = :login;",
        login=github_data["login"],
    ).all()
    if len(check) == 0:
        username = github_data["login"]
    else:
        username = github_data["login"] + str(random.randint(1, 99999))

    # Create user entry in database
    exec_query(
        conn,
        'INSERT INTO users (username, role, bio, github_id, token, profile_icon) VALUES (:g_login, "default", "A new Datapack Hub user!", :id, :token, :avatar)',
        g_login=username,
        id=github_data["id"],
        token=token,
        avatar=github_data["avatar_url"],
    )

    conn.commit()
    conn.close()

    print("CREATED USER: " + github_data["login"])

    return token



def get_user_ban_data(id: int) -> ShortBanData | None:
    conn = make_connection()

    banned_user = exec_query(
        conn,
        "select reason, expires from banned_users where id = :id",
        id=id,
    ).one_or_none()

    if banned_user is None:
        return None

    conn.close()

    return {"reason": banned_user[0], "expires": banned_user[1]}

@lru_cache
def user_owns_project(project: int, author: int) -> bool:
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


def send_notif(conn: Engine, title: str, msg: str, receiver: int) -> None:
    exec_query(
        conn,
        "INSERT INTO notifs VALUES (:title, :msg, False, 'default', :uid})",
        title=title,
        msg=msg,
        uid=receiver,
    )


if __name__ == "__main__":
    post.approval(
        "Silabear",
        "Hexenwerk",
        "Magic datapack which adds wands, spells, etc. and will soon even be well polished!",
        "https://files.datapackhub.net/icons/174209.png",
        "Flynecraft",
    )
