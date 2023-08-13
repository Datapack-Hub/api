from functools import lru_cache
import secrets
import sqlite3
import config
import utilities.post as post
import random

def create_user_account(
    ghubdata: dict,
):
    conn = sqlite3.connect(config.DATA + "data.db")

    token = secrets.token_urlsafe()
    
    check = conn.execute(f"select username from users where username = '{ghubdata['login']}';").fetchall()
    if len(check) == 0:
        username = ghubdata['login']
    else:
        username = ghubdata['login'] + str(random.randint(1,99999))

    # Create user entry in database
    conn.execute(
        f'INSERT INTO users (username, role, bio, github_id, token, profile_icon) VALUES ("{username}", "default", "A new Datapack Hub user!", {ghubdata["id"]}, "{token}", "{ghubdata["avatar_url"]}")'
    )

    conn.commit()
    conn.close()

    print("CREATED USER: " + ghubdata["login"])

    return token


@lru_cache
def get_user_ban_data(id: int):
    conn = sqlite3.connect(config.DATA + "data.db")

    banned_user = conn.execute(
        "select reason, expires from banned_users where id = " + str(id)
    ).fetchone()

    if not banned_user:
        return None

    conn.close()

    return {"reason": banned_user[0], "expires": banned_user[1]}


@lru_cache
def user_owns_project(project: int, author: int):
    conn = sqlite3.connect(config.DATA + "data.db")
    proj = conn.execute(
        f"select rowid from projects where rowid = {str(project)} and author = {str(author)}"
    ).fetchall()
    conn.close()
    return len(proj) == 1


def clean(query: str):
    return query.replace("'", r"''").replace(";", r"\;")


# def get_user_data(id: int, data: list[str])
#     conn = sqlite3.connect(config.DATA + "data.db")
#     query_props = ",".join(data)
#     user = conn.execute(
#         f"SELECT {clean(query_props)} FROM users WHERE rowid = {str(id)}"
#     ).fetchone()
#     conn.close()
#     return [*user]


if __name__ == "__main__":
    post.approval(
        "Silabear",
        "Hexenwerk",
        "Magic datapack which adds wands, spells, etc. and will soon even be well polished!",
        "https://files.datapackhub.net/icons/174209.png",
        "Flynecraft",
    )
