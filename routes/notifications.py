"""
**Notifications API endpoints**
"""

import sqlite3

from flask import Blueprint, request

import utilities.auth_utils
import utilities.post
from utilities import util

notifs = Blueprint("notifications", __name__, url_prefix="/notifs")


@notifs.route("/")
def all():
    if not request.headers.get("Authorization"):
        return "Authorization required", 401

    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))

    if usr == 32:
        return "Please make sure authorization type = Basic", 400

    if usr == 33:
        return "Token Expired", 401

    conn = util.make_connection()
    notifs = util.exec_query(
        conn,
        "select rowid, message, description, read, type from notifs where user = :id order by rowid desc limit 20",
        id=usr.id,
    ).all()

    res = [
        {"id": i[0], "message": i[1], "description": i[2], "read": i[3], "type": i[4]}
        for i in notifs
    ]

    # Mark as read
    for i in res:
        if i["read"] is False:
            util.exec_query(
                conn, "UPDATE notifs SET read = 1 WHERE rowid = :id", id=i["id"]
            )

    conn.commit()
    conn.close()

    return {"count": len(res), "result": res}


@notifs.route("/unread")
def unread():
    if not request.headers.get("Authorization"):
        return "Authorization required", 401

    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))

    if usr == 32:
        return "Please make sure authorization type = Basic", 400

    if usr == 33:
        return "Token Expired", 401

    conn = util.make_connection()
    notifs = util.exec_query(
        conn,
        "select rowid, message, description, read, type from notifs where user = :id and read = 0 order by rowid desc",
        id=usr.id,
    ).all()

    res = [
        {"id": i[0], "message": i[1], "description": i[2], "read": i[3], "type": i[4]}
        for i in notifs
    ]

    conn.commit()
    conn.close()

    return {"count": len(res), "result": res}


@notifs.route("/send/<int:target>", methods=["POST"])
def send(target):
    if not request.headers.get("Authorization"):
        return "Authorization required", 401

    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic", 400
    if usr == 33:
        return "Token Expired", 401

    if usr.role not in ["admin", "developer", "moderator", "helper"]:
        return "You are not allowed to do this!", 403

    notif_data = request.get_json(force=True)

    conn = util.make_connection()
    try:
        util.exec_query(
            conn,
            "INSERT INTO notifs VALUES (:title, :msg, False, :type, :target)",
            title=notif_data["message"],
            msg=notif_data["description"],
            type=notif_data["type"],
            target=target,
        )
    except sqlite3.Error as er:
        return "There was a problem: " " ".join(er.args), 500

    conn.commit()
    conn.close()

    utilities.post.site_log(
        usr.username,
        "Sent a notification",
        f"Sent a `{notif_data['type']}` notification to `{target}`",
    )

    return "Successfully warned user!", 200


@notifs.route("/delete/<int:id>", methods=["DELETE"])
def delete(id):
    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic", 400

    if usr == 33:
        return "Token Expired", 401

    conn = util.make_connection()
    notif = util.exec_query(
        conn, "SELECT user FROM notifs WHERE rowid = :id", id=id
    ).one()

    if usr.id != notif[0]:
        return "Not your notif!", 403
    try:
        util.exec_query(conn, "DELETE FROM notifs WHERE rowid = :id", id=id)
        conn.commit()
    except sqlite3.Error:
        return "Something bad happened", 500
    else:
        conn.close()
        return "worked fine"
