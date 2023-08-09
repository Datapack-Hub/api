"""
** Comments API endpoints**
"""

import sqlite3
from flask import Blueprint, request
import config
import utilities.auth_utils
import utilities.get_user
import utilities.util as util
import time
import regex

comments = Blueprint("comments", __name__, url_prefix="/comments")


@comments.route("/thread/<int:thread>")
def messages_from_thread(thread: int):
    conn = sqlite3.connect(config.DATA + "data.db")
    cmts = conn.execute(
        f"select rowid, message, author, sent from comments where thread_id = {thread} and parent_id is null order by sent desc"
    ).fetchall()

    out = []
    for cmt in cmts:
        author = utilities.get_user.from_id(cmt[2])
        replies = conn.execute(
            f"select rowid, message, author, sent from comments where thread_id = {thread} and parent_id = {cmt[0]} order by sent desc"
        ).fetchall()
        reps = []
        for reply in replies:
            repl_auth = utilities.get_user.from_id(reply[2])
            reps.append(
                {
                    "id": reply[0],
                    "message": reply[1],
                    "author": {
                        "username": repl_auth.username,
                        "id": repl_auth.id,
                        "role": repl_auth.role,
                        "bio": repl_auth.bio,
                        "profile_icon": repl_auth.profile_icon,
                        "badges": repl_auth.badges,
                    },
                    "sent": reply[3],
                }
            )
        out.append(
            {
                "id": cmt[0],
                "message": cmt[1],
                "author": {
                    "username": author.username,
                    "id": author.id,
                    "role": author.role,
                    "bio": author.bio,
                    "profile_icon": author.profile_icon,
                    "badges": author.badges,
                },
                "sent": cmt[3],
                "replies": reps,
            }
        )
    return {"count": out.__len__(), "result": out}


@comments.route("/thread/<int:thread>/post", methods=["POST"])
def post_msg(thread: int):
    if not request.headers.get("Authorization"):
        return "Authorization required", 400
    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic", 400
    if usr == 33:
        return "Token Expired", 401

    conn = sqlite3.connect(config.DATA + "data.db")
    cmt_data = request.get_json(True)
    try:
        cmt_data["message"]
    except KeyError:
        return "You need to provide a message field!", 400

    try:
        mentions = regex.findall("@(\w+)")
        for user in mentions:
            user = utilities.get_user.from_username(user)
            if user:
                auth = conn.execute(
                    "select author, title, url from projects where rowid = "
                    + str(thread)
                ).fetchone()
                conn.execute(
                    f"INSERT INTO notifs VALUES ('You were mentioned', '[{usr.username}](https://datapackhub.net/user/{usr.username}) mentioned you in a comment on project [{auth[1]}](https://datapackhub.net/project/{auth[2]}).', False,  'default', {auth[0]})"
                )
        try:
            cmt_data["parent_id"]
        except KeyError:
            conn.execute(
                f"INSERT INTO comments VALUES ({thread}, '{util.clean(cmt_data['message'])}', {usr.id}, {time.time()}, null)"
            )

            auth = conn.execute(
                "select author, title, url from projects where rowid = " + str(thread)
            ).fetchone()

            # Notify author
            if usr.id != auth[0]:
                conn.execute(
                    f"INSERT INTO notifs VALUES ('New comment', '[{usr.username}](https://datapackhub.net/user/{usr.username}) left a comment on your project [{auth[1]}](https://datapackhub.net/project/{auth[2]}).', False,  'default', {auth[0]})"
                )
        else:
            conn.execute(
                f"INSERT INTO comments VALUES ({thread}, '{util.clean(cmt_data['message'])}', {usr.id}, {time.time()}, {cmt_data['parent_id']})"
            )

            auth = conn.execute(
                "select author from comments where rowid = "
                + str(cmt_data["parent_id"])
            ).fetchone()

            # Notify author
            if (
                usr.id != auth[0]
            ):  # I got bored and added my suggestion myself -HoodieRocks
                proj = conn.execute(
                    "select title, url from projects where rowid = " + str(thread)
                ).fetchone()

                conn.execute(
                    f"INSERT INTO notifs VALUES ('New reply', '[{usr.username}](https://datapackhub.net/user/{usr.username}) left a reply to your comment on project [{proj[0]}](https://datapackhub.net/project/{proj[1]}).', False,  'default', {auth[0]})"
                )
    except sqlite3.Error as er:
        conn.rollback()
        conn.close()
        return "There was an error! " + " ".join(er.args), 500

    conn.commit()
    conn.close()

    return "Posted comment!", 200


@comments.route("/id/<int:id>", methods=["GET", "DELETE"])
def get_comment(id: int):
    if request.method == "GET":
        conn = sqlite3.connect(config.DATA + "data.db")
        comment = conn.execute(
            f"select rowid, message, author, sent from comments where rowid = {id} and parent_id is null order by sent desc"
        ).fetchall()

        if len(comment) == 0:
            return "Not found.", 404

        comment = comment[0]

        author = utilities.get_user.from_id(comment[2])

        replies = conn.execute(
            f"select rowid, message, author, sent from comments where parent_id = {id} order by sent desc"
        ).fetchall()
        reps = []
        for reply in replies:
            repl_auth = utilities.get_user.from_id(reply[2])
            reps.append(
                {
                    "id": reply[0],
                    "message": reply[1],
                    "author": {
                        "username": repl_auth.username,
                        "id": repl_auth.id,
                        "role": repl_auth.role,
                        "bio": repl_auth.bio,
                        "profile_icon": repl_auth.profile_icon,
                        "badges": repl_auth.badges,
                    },
                    "sent": reply[3],
                }
            )

        return {
            "id": comment[0],
            "message": comment[1],
            "author": {
                "username": author.username,
                "id": author.id,
                "role": author.role,
                "bio": author.bio,
                "profile_icon": author.profile_icon,
                "badges": author.badges,
            },
            "sent": comment[3],
            "replies": reps,
        }
    elif request.method == "DELETE":
        conn = sqlite3.connect(config.DATA + "data.db")
        comment = conn.execute(
            f"select rowid, message, author, sent from comments where rowid = {id} and parent_id is null order by sent desc"
        ).fetchall()

        if len(comment) == 0:
            return "Not found.", 404

        comment = comment[0]

        if not request.headers.get("Authorization"):
            conn.close()
            return "Authorization required", 400
        usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
        if usr == 32:
            conn.close()
            return "Please make sure authorization type = Basic", 400
        if usr == 33:
            conn.close()
            return "Token Expired", 401

        if not (usr.id == comment[2] or usr.role in ["admin", "moderator"]):
            conn.close()
            return "This isn't your comment.", 403

        conn.execute(f"delete from comments where rowid = {id}")
        conn.execute(f"delete from comments where parent_id = {id}")

        conn.commit()
        conn.close()
        return "Deleted comment."
