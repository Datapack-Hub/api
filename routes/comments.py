"""
** Comments API endpoints**
"""

import sqlite3
from flask import Blueprint
import config

comments = Blueprint("comments", __name__, url_prefix="/comments")


@comments.route("/thread/<int:thread>")
def messages_from_thread(thread: int):
    conn = sqlite3.connect(config.DATA + "data.db")
    cmts = conn.execute(
        f"select rowid, message, author, sent from comments where thread_id = {thread} and parent_id is null"
    ).fetchall()

    out = []
    for cmt in cmts:
        replies = conn.execute(
            f"select rowid, message, author, sent from comments where thread_id = {thread} and parent_id = {cmt[0]}"
        ).fetchall()
        reps = []
        for reply in replies:
            reps.append(
                {
                    "id": reply[0],
                    "message": reply[1],
                    "author": reply[2],
                    "sent": reply[4],
                }
            )
        out.append(
            {
                "id": cmt[0],
                "message": cmt[1],
                "author": cmt[2],
                "sent": cmt[4],
                "replies": reps,
            }
        )
    return {"count":out.__len__(), "result":out}
