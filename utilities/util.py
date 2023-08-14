from functools import lru_cache
import secrets

from sqlalchemy import Connection, CursorResult, Engine, create_engine, text
import config
import utilities.post as post
import random


def make_connection() -> Connection:
    return create_engine("sqlite:///" + config.DATA + "data.db").connect()


def exec_query(conn: Connection, query: str, **params) -> CursorResult:
    q = text(query)

    if params:
        q = q.bindparams(**params)
    return conn.execute(q)


def create_user_account(
    github_data: dict,
):
    conn = make_connection()

    token = secrets.token_urlsafe()

    check = exec_query(
        conn,
        "select username from users where username = :login;",
        params={"login": github_data["login"]},
    ).fetchall()
    if len(check) == 0:
        username = github_data["login"]
    else:
        username = github_data["login"] + str(random.randint(1, 99999))

    # Create user entry in database
    exec_query(
        conn,
        'INSERT INTO users (username, role, bio, github_id, token, profile_icon) VALUES (:g_login, "default", "A new Datapack Hub user!", :id, :token, :avatar)',
        params={
            "g_login": username,
            "id": github_data["id"],
            "token": token,
            "avatar": github_data["avatar_url"],
        },
    )

    conn.commit()
    conn.close()

    print("CREATED USER: " + github_data["login"])

    return token


@lru_cache
def get_user_ban_data(id: int):
    conn = make_connection()

    banned_user = exec_query(
        conn,
        "select reason, expires from banned_users where id = :id",
        params={"id": id},
    ).fetchone()

    if not banned_user:
        return None

    conn.close()

    return {"reason": banned_user[0], "expires": banned_user[1]}


@lru_cache
def user_owns_project(project: int, author: int):
    conn = make_connection()
    proj = exec_query(
        conn,
        "select rowid from projects where rowid = :project and author = :author",
        params={"project": project, "author": author},
    ).fetchall()
    conn.close()
    return len(proj) == 1


def clean(query: str):
    return query.replace("'", r"''").replace(";", r"\;")


# def get_user_data(id: int, data: list[str])
#     conn = create_engine("sqlite://"  + config.DATA + "data.db")
#     query_props = ",".join(data)
#     user = conn.execute(
#         f"SELECT {clean(query_props)} FROM users WHERE rowid = {str(id)}"
#     ).fetchone()
#     conn.close()
#     return [*user]


def send_notif(conn: Engine, title: str, msg: str, receiver: int):
    exec_query(
        conn,
        "INSERT INTO notifs VALUES (:title, :msg, False, 'default', :uid})",
        params={
            "title": title,
            "msg": msg,
            "uid": receiver,
        },
    )


if __name__ == "__main__":
    post.approval(
        "Silabear",
        "Hexenwerk",
        "Magic datapack which adds wands, spells, etc. and will soon even be well polished!",
        "https://files.datapackhub.net/icons/174209.png",
        "Flynecraft",
    )
