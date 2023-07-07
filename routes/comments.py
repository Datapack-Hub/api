"""
** Comments API endpoints**
"""

import sqlite3
from flask import Blueprint, request
import config
import usefuls.util as util
import time

comments = Blueprint("comments", __name__, url_prefix="/comments")


@comments.route("/thread/<int:thread>")
def messages_from_thread(thread: int):
    conn = sqlite3.connect(config.DATA + "data.db")
    cmts = conn.execute(
        f"select rowid, message, author, sent from comments where thread_id = {thread} and parent_id is null"
    ).fetchall()

    out = []
    for cmt in cmts:
        author = util.get_user.from_id(cmt[2])
        replies = conn.execute(
            f"select rowid, message, author, sent from comments where thread_id = {thread} and parent_id = {cmt[0]}"
        ).fetchall()
        reps = []
        for reply in replies:
            repl_auth = util.get_user.from_id(reply[2])
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
        return "Authorization required", 401
    usr = util.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic"
    if usr == 33:
        return "Token Expired", 498

    conn = sqlite3.connect(config.DATA + "data.db")
    cmt_data = request.get_json(True)
    try:
        cmt_data["message"]
    except:
        return "You need to provide a message field!", 400

    try:
        cmt_data["parent_id"]
    except:
        conn.execute(
            f"INSERT INTO comments VALUES ({thread}, '{util.sanitise(cmt_data['message'])}', {usr.id}, {time.time()}, null)"
        )
    else:
        conn.execute(
            f"INSERT INTO comments VALUES ({thread}, '{util.sanitise(cmt_data['message'])}', {usr.id}, {time.time()}, {cmt_data['parent_id']})"
        )

    conn.commit()
    conn.close()

    return "Posted comment!", 200
