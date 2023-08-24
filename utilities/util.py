import random
import secrets
from functools import lru_cache

from sqlalchemy import Engine
import sqlalchemy as sq

from utilities import post
from utilities.commons import ProjectModel, UserModel
from utilities.db_utils import exec_query, make_session, make_connection


def create_user_account(
    github_data: dict,
):
    conn = make_session()

    token = secrets.token_urlsafe()

    check = conn.execute(
        sq.select(UserModel.username).where(
            UserModel.username == github_data["login"]
        )
    ).all()

    username = github_data["login"]
    if len(check) > 0:
        username = github_data["login"] + str(random.randint(1, 99999))

    # Create user entry in database

    conn.execute(
        sq.insert(UserModel).values(
            username=username,
            role="default",
            bio="A new Datapack Hub user!",
            github_id=github_data["id"],
            token=token,
            profile_icon=github_data["avatar_url"],
        )
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
        id=id,
    ).one()

    if not banned_user:
        return None

    conn.close()

    return {"reason": banned_user[0], "expires": banned_user[1]}


@lru_cache
def user_owns_project(project: int, author: int):
    conn = make_session()

    proj = conn.execute(
        sq.select(ProjectModel.rowid).where(
            ProjectModel.rowid == project and ProjectModel.author == author
        )
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


if __name__ == "__main__":
    post.approval(
        "Silabear",
        "Hexenwerk",
        "Magic datapack which adds wands, spells, etc. and will soon even be well polished!",
        "https://files.datapackhub.net/icons/174209.png",
        "Flynecraft",
    )
