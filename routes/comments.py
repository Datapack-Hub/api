"""
**Notifications API endpoints**
"""

from flask import Blueprint, request
import usefuls.util as util
import sqlite3
import config

comments = Blueprint("comments", __name__, url_prefix="/comments")


def get_comment_chain(parent: int):
    conn = sqlite3.connect(config.DATA + "data.db")
    parent = conn.execute(
        f"select rowid, message, author, replies, sent from comments where rowid = {parent}"
    ).fetchone()

    if not parent[3]:
        return {
            "id": parent[0],
            "message": parent[1],
            "author": parent[2],
            "sent": parent[4],
        }

    parent = {
        "id": parent[0],
        "message": parent[1],
        "author": parent[2],
        "sent": parent[4],
        "replies": [],
    }

    replies = str(parent[3]).split(" ")
    for i in replies:
        # something
        pass


@comments.route("/thread/<int:thread>")
def messages_from_thread(thread: int):
    conn = sqlite3.connect(config.DATA + "data.db")
    cmts = conn.execute(
        f"select rowid, message, author, replies, sent from comments where thread = {thread} and replied_to = null"
    ).fetchall()

    out = []
    for cmt in cmts:
        if cmt[3]:
            replies = conn.execute(
                f"select rowid, message, author, replies, sent from comments where thread = {thread} and replied_to = null"
            )
        out.append({"id": cmt[0], "message": cmt[1], "author": cmt[2], "sent": cmt[4]})
