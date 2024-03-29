"""
** Comments API endpoints**
"""

import sqlite3
import time
from typing import Any

import regex
from flask import Blueprint, request

import utilities.auth_utils
import utilities.get_user
from utilities import util

comments = Blueprint("comments", __name__, url_prefix="/comments")


@comments.route("/thread/<int:thread>")
def messages_from_thread(thread: int) -> tuple[dict[str, Any] | str, int]:
    conn = util.make_connection()
    cmts = util.exec_query(
        conn,
        "select rowid, message, author, sent from comments where thread_id = :thread and parent_id is null order by sent desc",
        thread=thread,
    ).all()

    out: list[dict[str, Any]] = []
    for cmt in cmts:
        author = utilities.get_user.from_id(cmt[2])

        if author is None:
            return "User is not defined!", 400
        replies = util.exec_query(
            conn,
            "select rowid, message, author, sent from comments where thread_id = :thread and parent_id = :comment order by sent desc",
            thread=thread,
            comment=cmt[0],
        ).all()
        reps: list[dict[str, Any]] = []
        for reply in replies:
            repl_auth = utilities.get_user.from_id(reply[2])

            if repl_auth is None:
                return "User is not defined!", 400

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
    return {"count": out.__len__(), "result": out}, 200


@comments.route("/thread/<int:thread>/post", methods=["POST"])
def post_msg(thread: int):
    if not request.headers.get("Authorization"):
        return "Authorization required", 400
    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic", 400
    if usr == 31:
        return "Provide Authorization header", 400
    if usr == 33:
        return "Token Expired", 401

    cmt_data = request.get_json(force=True)
    try:
        cmt_data["message"]
    except KeyError:
        return "You need to provide a message field!", 400

    conn = util.make_connection()
    try:
        mentions = regex.findall(r"@(\w+)", cmt_data["message"])
        for user in mentions:
            if utilities.get_user.from_username(user):
                auth = util.exec_query(
                    conn,
                    "select author, title, url from projects where rowid = :thread",
                    thread=thread,
                ).one()
                util.exec_query(
                    conn,
                    "INSERT INTO notifs VALUES (:title, :msg, False, :type, :uid)",
                    title="You were mentioned!",
                    msg=f"[{usr.username}](https://datapackhub.net/user/{usr.username}) mentioned you in a comment on project [{auth[1]}](https://datapackhub.net/project/{auth[2]}).",
                    type="default",
                    uid=auth[0],
                )
        try:
            cmt_data["parent_id"]
        except KeyError:
            util.exec_query(
                conn,
                "INSERT INTO comments VALUES (:thread, :msg, :uid, :time, null)",
                thread=thread,
                msg=cmt_data["message"],
                uid=usr.id,
                time=time.time(),
            )

            auth = util.exec_query(
                conn,
                "select author, title, url from projects where rowid = :thread",
                thread=thread,
            ).one()

            # Notify author
            if usr.id != auth[0]:
                util.exec_query(
                    conn,
                    "INSERT INTO notifs VALUES ('New comment', :msg, False,  'default', :uid)",
                    msg=f"[{usr.username}](https://datapackhub.net/user/{usr.username}) left a comment on your project [{auth[1]}](https://datapackhub.net/project/{auth[2]}).",
                    uid=auth[0],
                )
        else:
            util.exec_query(
                conn,
                "INSERT INTO comments VALUES (:thread, :msg, :uid, :time, :pid)",
                uid=usr.id,
                time=time.time(),
                pid=cmt_data["parent_id"],
                msg=cmt_data["message"],
                thread=thread,
            )

            auth = util.exec_query(
                conn,
                "select author from comments where rowid = :pid",
                pid=cmt_data["parent_id"],
            ).one()

            # Notify author
            if (
                usr.id != auth[0]
            ):  # I got bored and added my suggestion myself -HoodieRocks
                proj = util.exec_query(
                    conn,
                    "select title, url from projects where rowid = :thread",
                    thread=thread,
                ).one()

                util.exec_query(
                    conn,
                    "INSERT INTO notifs VALUES ('New reply', :msg, False,  'default', :uid)",
                    msg=f"[{usr.username}](https://datapackhub.net/user/{usr.username}) left a reply to your comment on project [{proj[0]}](https://datapackhub.net/project/{proj[1]}).",
                    uid=auth[0],
                )
    except sqlite3.Error as er:
        conn.rollback()

        return f"There was an error! {' '.join(er.args)}", 500

    conn.commit()

    return "Posted comment!", 200


@comments.route("/id/<int:id>", methods=["GET", "DELETE"])
def get_comment(id: int) -> tuple[dict[str, Any] | str, int]:
    if request.method == "GET":
        conn = util.make_connection()
        comment = util.exec_query(
            conn,
            "select rowid, message, author, sent from comments where rowid = :id and parent_id is null order by sent desc",
            id=id,
        ).all()

        if not comment:
            return "Not found.", 404

        comment = comment[0]

        author = utilities.get_user.from_id(comment[2])

        if author is None:
            return "Something went wrong!", 500

        replies = util.exec_query(
            conn,
            "select rowid, message, author, sent from comments where parent_id = :id order by sent desc",
            id=id,
        ).all()
        reps = []
        for reply in replies:
            repl_auth = utilities.get_user.from_id(reply[2])

            if repl_auth is None:
                return "We don't know how this happened, but it did", 500

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
        }, 200
    elif request.method == "DELETE":
        conn = util.make_connection()
        comment = util.exec_query(
            conn,
            "select rowid, message, author, sent, parent_id from comments where rowid = :id order by sent desc",
            id=id,
        ).all()

        if not comment:
            return "Not found.", 404

        comment = comment[0]

        if not request.headers.get("Authorization"):
            return "Authorization required", 400
        usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
        if usr == 32:
            return "Please make sure authorization type = Basic", 400
        if usr == 31:
            return "Provide Authorization header", 400
        if usr == 33:
            return "Token Expired", 401

        if not (usr.id == comment[2] or usr.role in ["admin", "moderator"]):
            return "This isn't your comment.", 403

        if comment[4] is None:
            util.exec_query(conn, "delete from comments where rowid = :id", id=id)
            util.exec_query(conn, "delete from comments where parent_id = :id", id=id)
        else:
            util.exec_query(conn, "delete from comments where rowid = :id", id=id)

        conn.commit()

        return "Deleted comment.", 200
    return "HTTP Method disallowed", 400
