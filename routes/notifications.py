"""
**Notifications API endpoints**
"""

from flask import Blueprint, request
import usefuls.util as util
import sqlite3
import config

notifs = Blueprint("notifications", __name__, url_prefix="/notifs")


@notifs.route("/")
def all():
    if not request.headers.get("Authorization"):
        return "Authorization required", 401

    usr = util.authenticate(request.headers.get("Authorization"))

    if usr == 32:
        return "Please make sure authorization type = Basic"

    if usr == 33:
        return "Token Expired", 498

    conn = sqlite3.connect(config.DATA + "data.db")
    notifs = conn.execute(
        f"select rowid, message, description, read, type from notifs where user = {usr.id} order by rowid desc limit 20"
    ).fetchall()

    res = []

    for i in notifs:
        res.append(
            {
                "id": i[0],
                "message": i[1],
                "description": i[2],
                "read": i[3],
                "type": i[4],
            }
        )

    # Mark as read
    for i in res:
        if i["read"] is False:
            conn.execute("UPDATE notifs SET read = 1 WHERE rowid = " + str(i["id"]))

    conn.commit()
    conn.close()

    return {"count": len(res), "result": res}


@notifs.route("/unread")
def unread():
    if not request.headers.get("Authorization"):
        return "Authorization required", 401

    usr = util.authenticate(request.headers.get("Authorization"))

    if usr == 32:
        return "Please make sure authorization type = Basic"

    if usr == 33:
        return "Token Expired", 498

    conn = sqlite3.connect(config.DATA + "data.db")
    notifs = conn.execute(
        f"select rowid, message, description, read, type from notifs where user = {usr.id} and read = 0 order by rowid desc"
    ).fetchall()

    res = []

    for i in notifs:
        res.append(
            {
                "id": i[0],
                "message": i[1],
                "description": i[2],
                "read": i[3],
                "type": i[4],
            }
        )
        if i[3] is False:
            conn.execute("UPDATE notifs SET read = True WHERE rowid = " + str(i[0]))

    conn.commit()
    conn.close()

    return {"count": len(res), "result": res}


@notifs.route("/send/<int:target>", methods=["POST"])
def send(target):
    if not request.headers.get("Authorization"):
        return "Authorization required", 401

    usr = util.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic"
    if usr == 33:
        return "Token Expired", 498

    if usr.role not in ["admin", "developer", "moderator", "helper"]:
        return "You are not allowed to do this!", 403

    notif_data = request.get_json(force=True)

    conn = sqlite3.connect(config.DATA + "data.db")
    try:
        conn.execute(
            f"INSERT INTO notifs VALUES ('{util.sanitise(notif_data['message'])}', '{util.sanitise(notif_data['description'])}', False, {target}, '{util.sanitise(notif_data['type'])}')"
        )
    except sqlite3.Error as er:
        return "There was a problem: " " ".join(er.args), 500
    
    conn.commit()
    conn.close()

    util.post_site_log(
        usr.username,
        "Sent a notification",
        f"Sent a `{notif_data['type']}` notification to `{target}`",
    )

    return "Successfully warned user!", 200


@notifs.route("/delete/<int:id>", methods=["DELETE"])
def delete(id):
    usr = util.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic"

    if usr == 33:
        return "Token Expired", 498

    conn = sqlite3.connect(config.DATA + "data.db")
    notif = conn.execute("SELECT user FROM notifs WHERE rowid = " + str(id)).fetchone()

    if usr.id != notif[0]:
        return "Not your notif!", 403
    try:
        conn.execute("DELETE FROM notifs WHERE rowid = " + str(id))
        conn.commit()
    except:
        return "Something bad happened", 500
    else:
        conn.close()
        return "worked fine"