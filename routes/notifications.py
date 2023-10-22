"""
**Notifications API endpoints**
"""

import sqlite3

from fastapi import APIRouter, HTTPException, Request

import utilities.auth_utils
from utilities.request_types import SendNotifBody
import utilities.weblogs
from utilities import util

notifs = APIRouter("notifications", __name__, url_prefix="/notifs")


@notifs.get("/")
def get_all_notifs(request: Request):
    if not request.headers.get("Authorization"):
        raise HTTPException(401, "Token required!")

    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))

    if usr == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")

    if usr == 33:
        raise HTTPException(401, "Token Expired")

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

    return {"count": len(res), "result": res}


@notifs.get("/unread")
def get_unread_notifs(request: Request):
    if not request.headers.get("Authorization"):
        raise HTTPException(401, "Authorization required")

    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))

    if usr == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")

    if usr == 33:
        raise HTTPException(401, "Token Expired")

    notifs = util.commit_query(
        "select rowid, message, description, read, type from notifs where user = :id and read = 0 order by rowid desc",
        id=usr.id,
    ).all()

    res = [
        {"id": i[0], "message": i[1], "description": i[2], "read": i[3], "type": i[4]}
        for i in notifs
    ]

    return {"count": len(res), "result": res}


@notifs.post("/send/{target}")
def send_notif(target: int, request: Request, notif_data: SendNotifBody):
    if not request.headers.get("Authorization"):
        raise HTTPException(401, "Authorization required")

    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))

    if usr == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")

    if usr == 33:
        raise HTTPException(401, "Token Expired")

    if usr.role not in ["admin", "developer", "moderator", "helper"]:
        raise HTTPException(403, "No permission")
    
    conn = util.make_connection()
    try:
        util.exec_query(
            conn,
            "INSERT INTO notifs VALUES (:title, :msg, False, :type, :target)",
            title=notif_data.message,
            msg=notif_data.description,
            type=notif_data.type,
            target=target,
        )
    except sqlite3.Error as er:
        conn.rollback()

        raise HTTPException(500, "There was a problem: ".join(er.args)) from er

    conn.commit()

    utilities.weblogs.site_log(
        usr.username,
        "Sent a notification",
        f"Sent a `{notif_data.type}` notification to `{target}`",
    )

    return "Successfully warned user!"


@notifs.route("/delete/{id}", methods=["DELETE"])
def delete_notif(id: int, request: Request):
    if not request.headers.get("Authorization"):
        raise HTTPException(401, "Authorization required")

    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))

    if usr == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")

    if usr == 33:
        raise HTTPException(401, "Token Expired")

    conn = util.make_connection()
    notif = util.exec_query(
        conn, "SELECT user FROM notifs WHERE rowid = :id", id=id
    ).one()

    if usr.id != notif[0]:
        raise HTTPException(403, "Not your notif")
    try:
        util.exec_query(conn, "DELETE FROM notifs WHERE rowid = :id", id=id)
        conn.commit()
    except sqlite3.Error as err:
        conn.rollback()

        raise HTTPException(500, "Something bad happened") from err
    else:
        return "worked fine"
