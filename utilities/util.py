from functools import lru_cache
import secrets

from sqlalchemy import Engine, create_engine, text
import config
import utilities.post as post
import random


def create_user_account(
    github_data: dict,
):
    conn = create_engine(config.DATA + "data.db")

    token = secrets.token_urlsafe()

    check = conn.execute(
        text("select username from users where username = :login;"),
        login=github_data['login']
    ).fetchall()
    if len(check) == 0:
        username = github_data["login"]
    else:
        username = github_data["login"] + str(random.randint(1, 99999))

    # Create user entry in database
    conn.execute(
        text(
            'INSERT INTO users (username, role, bio, github_id, token, profile_icon) VALUES (:g_login, "default", "A new Datapack Hub user!", :id, :token, :avatar)'
        ),
        g_login=username,
        id=github_data["id"],
        token=token,
        avatar=github_data["avatar_url"],
    )

    conn.commit()
    conn.close()

    print("CREATED USER: " + github_data["login"])

    return token


@lru_cache
def get_user_ban_data(id: int):
    conn = create_engine(config.DATA + "data.db")

    banned_user = conn.execute(
        text("select reason, expires from banned_users where id = :id"), id=id
    ).fetchone()

    if not banned_user:
        return None

    conn.close()

    return {"reason": banned_user[0], "expires": banned_user[1]}


@lru_cache
def user_owns_project(project: int, author: int):
    conn = create_engine(config.DATA + "data.db")
    proj = conn.execute(
        text("select rowid from projects where rowid = :project and author = :author"),
        project=project,
        author=author,
    ).fetchall()
    conn.close()
    return len(proj) == 1


def clean(query: str):
    return query.replace("'", r"''").replace(";", r"\;")


# def get_user_data(id: int, data: list[str])
#     conn = create_engine(config.DATA + "data.db")
#     query_props = ",".join(data)
#     user = conn.execute(
#         f"SELECT {clean(query_props)} FROM users WHERE rowid = {str(id)}"
#     ).fetchone()
#     conn.close()
#     return [*user]


def send_notif(conn: Engine, title: str, msg: str, receiver: int):
    conn.execute(
        text("INSERT INTO notifs VALUES (:title, :msg, False, 'default', :uid})"),
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
