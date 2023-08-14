"""
**Moderation API endpoints**
"""

import difflib
import json
import random
import shlex
import sqlite3
import time
from datetime import date
import bleach

import requests
from flask import Blueprint, request
from flask_cors import CORS
from sqlalchemy import create_engine, text

import config
import gen_example_data
import utilities.auth_utils
import utilities.get_user as get_user
import utilities.post
import utilities.util as util

console_commands = [
    "sql",
    "select",
    "hello",
    "reset",
    "notify",
    "user",
    "backup",
    "restore",
]


def auth(token: str, perm_levels: list[str]):
    if not token:
        return False

    user = utilities.auth_utils.authenticate(token)

    if user == 33:
        return 33

    if user.role not in perm_levels:
        return False
    return user


mod = Blueprint("mod", __name__, url_prefix="/moderation")

CORS(mod, supports_credentials=True)


@mod.route("/console", methods=["POST"])
def console():
    data = json.loads(request.data)
    full = data["command"]
    args = shlex.split(data["command"])
    cmd = args[0]

    del args[0]

    if cmd not in console_commands:
        closest = difflib.get_close_matches(cmd, console_commands)
        if len(closest) >= 1:
            return (
                f"Error: Command {bleach.clean(cmd)} not found. Did you mean {bleach.clean(closest[0])}?",
                400,
            )
        else:
            return f"Error: Command {bleach.clean(cmd)} not found.", 400

    # Check user authentication status
    if not utilities.get_user.from_token(request.headers.get("Authorization")[6:]):
        return "hey u! sign in again plz (i am not hax)", 401

    utilities.post.site_log(
        utilities.get_user.from_token(
            request.headers.get("Authorization")[6:]
        ).username,
        "Ran console command",
        f"Ran the console command: `{data['command']}`",
    )

    if cmd == "sql":
        # Check auth
        if not auth(request.headers.get("Authorization"), ["admin"]):
            return "You do not have permission to run this command!"

        sql_command = full[3:]

        # Run SQLITE command
        try:
            conn = create_engine("sqlite://" + config.DATA + "data.db")
            conn.execute(sql_command)
            conn.commit()
            conn.close()
        except sqlite3.Error as error:
            return "SQL Error: " + (" ".join(error.args)), 400
        else:
            return "Processed SQL command!", 200

    elif cmd == "select":
        if not auth(request.headers.get("Authorization"), ["admin"]):
            return "You do not have permission to run this command!"

        sql_command = "SELECT " + full[7:]

        # Run SQLITE command
        try:
            conn = create_engine("sqlite://" + config.DATA + "data.db")
            out = conn.execute(sql_command).fetchall()
            conn.commit()
            conn.close()
        except sqlite3.Error as error:
            return "SQL Error: " + (" ".join(error.args)), 400
        else:
            return (
                bleach.clean(json.dumps(out, indent=3).replace("\n", "<br />"), ["br"]),
                200,
            )
    elif cmd == "user":
        if not auth(request.headers.get("Authorization"), ["admin", "moderator"]):
            return "You do not have permission to run this command!"

        # Run SQLITE command
        try:
            conn = create_engine("sqlite://" + config.DATA + "data.db")
            out = conn.execute(
                text(
                    "select username, role, rowid from users where trim(username) like :uname"
                ),
                uname=args[0],
            ).fetchall()
            conn.commit()
            conn.close()
        except sqlite3.Error as error:
            return "SQL Error: " + (" ".join(error.args)), 400
        else:
            return_this = ""
            for u in out:
                return_this += f"{u[0]} (ID {u[2]}) | Role: {u[1]}\n"
            return bleach.clean(return_this)
    elif cmd == "hello":
        return "Beep boop! Hi!"
    elif cmd == "reset":
        if (
            utilities.get_user.from_token(
                request.headers.get("Authorization")[6:]
            ).username
            != "Silabear"
        ):
            return "Only Silabear can run this command!", 403
        gen_example_data.reset(args[0])
        return "Reset the database."
    elif cmd == "backup":
        id = random.randint(1, 1000)
        if not auth(request.headers.get("Authorization"), ["admin"]):
            return "You do not have permission to run this command!"
        put = requests.put(
            "https://backups.datapackhub.net/"
            + date.today().strftime("custom-" + str(id)),
            open(config.DATA + "data.db", "rb"),
            headers={
                "Authorization": config.BACKUPS_TOKEN,
            },
            timeout=300,
        )

        if not put.ok:
            return "It didn't work."

        return "Backed up the database as " + str(id)
    elif cmd == "notify":
        if not auth(
            request.headers.get("Authorization"),
            ["admin", "developer", "moderator", "helper"],
        ):
            return "You can't run this command!", 403
        if len(args) < 3:
            return "Missing values!", 400
        conn = create_engine("sqlite://" + config.DATA + "data.db")
        try:
            conn.execute(
                text("INSERT INTO notifs VALUES (:arg1, :arg2, False, :arg0, :arg3)"),
                arg0=args[0],
                arg1=args[1],
                arg2=args[2],
                arg3=args[3],
            )
        except sqlite3.Error as er:
            return "Error: " + " ".join(er.args), 400
        conn.commit()
        conn.close()
        return "Notified the user!"


@mod.route("/log_out/<int:id>", methods=["post"])
def logout(id: int):
    # Check auth
    if not auth(
        request.headers.get("Authorization"), ["admin", "moderator", "developer"]
    ):
        return 403

    try:
        utilities.auth_utils.log_user_out(id)
    except:
        return "Failed", 500
    else:
        utilities.post.site_log(
            utilities.get_user.from_token(
                request.headers.get("Authorization")[6:]
            ).username,
            "Logged user out",
            f"Logged out user`{id}`",
        )
        return "Success!", 200


@mod.route("/ban/<int:user>", methods=["post", "delete"])
def ban(user: int):
    if not auth(
        request.headers.get("Authorization"), ["admin", "moderator", "developer"]
    ):
        return "Not allowed.", 403
    if request.method == "POST":
        # get time
        dat = request.get_json(force=True)
        current = time.time()
        expiry = current + (86400 * dat["expires"])

        conn = create_engine("sqlite://" + config.DATA + "data.db")
        try:
            conn.execute(
                text(
                    "insert into banned_users values (:user, :expiry, '{util.clean(dat['message'])}')"
                ),
                user=user,
                expiry=expiry,
            )
        except sqlite3.Error as er:
            return " ".join(er.args)
        else:
            conn.commit()
            conn.close()
            utilities.post.site_log(
                utilities.get_user.from_token(
                    request.headers.get("Authorization")[6:]
                ).username,
                "Banned User",
                f"Banned user `{utilities.get_user.from_id(user)}` for reason `{dat['message']}`",
            )
            return "worked fine"
    else:
        dat = request.get_json(force=True)
        conn = create_engine("sqlite://" + config.DATA + "data.db")
        try:
            conn.execute(text("delete from banned_users where self = :user"), user=user)
        except sqlite3.Error as er:
            return " ".join(er.args)
        else:
            conn.commit()
            conn.close()
            utilities.post.site_log(
                utilities.get_user.from_token(
                    request.headers.get("Authorization")[6:]
                ).username,
                "Unbanned User",
                f"Unbanned user `{utilities.get_user.from_id(user)}` for reason `{dat['message']}`",
            )
            return "worked fine"


@mod.route("/user/<int:id>")
def user_data(id):
    if not auth(
        request.headers.get("Authorization"), ["moderator", "developer", "admin"]
    ):
        return "You can't do this!", 403

    conn = create_engine("sqlite://" + config.DATA + "data.db")
    ban_data = conn.execute(
        text("SELECT * FROM banned_users WHERE id = :id"), id=id
    ).fetchall()

    if len(ban_data) == 0:
        return {"banned": False, "banMessage": None, "banExpiry": None}
    else:
        return {
            "banned": True,
            "banMessage": ban_data[0][2],
            "banExpiry": ban_data[0][1],
        }


@mod.route("/queue/<string:type>")
def queue(type: str):
    if not auth(
        request.headers.get("Authorization"),
        ["moderator", "admin"],
    ):
        return "You can't do this!", 403

    conn = create_engine("sqlite://" + config.DATA + "data.db")

    if type == "publish":
        r = conn.execute(
            "select type, author, title, icon, url, description, rowid, status from projects where status = 'publish_queue'"
        ).fetchall()

        # Form array
        out = []
        for item in r:
            author = get_user.from_id(item[1])
            out.append(
                {
                    "type": item[0],
                    "author": {
                        "username": author.username,
                        "id": author.id,
                        "role": author.role,
                        "bio": author.bio,
                        "profile_icon": author.profile_icon,
                        "badges": author.badges,
                    },
                    "title": item[2],
                    "icon": item[3],
                    "url": item[4],
                    "description": item[5],
                    "ID": item[6],
                    "status": item[7],
                }
            )

        conn.close()
        return {"count": len(out), "projects": out}
    elif type == "review":
        r = conn.execute(
            "select type, author, title, icon, url, description, rowid, status from projects where status = 'review_queue'"
        ).fetchall()

        # Form array
        out = []
        for item in r:
            author = get_user.from_id(item[1])
            out.append(
                {
                    "type": item[0],
                    "author": {
                        "username": author.username,
                        "id": author.id,
                        "role": author.role,
                        "bio": author.bio,
                        "profile_icon": author.profile_icon,
                        "badges": author.badges,
                    },
                    "title": item[2],
                    "icon": item[3],
                    "url": item[4],
                    "description": item[5],
                    "ID": item[6],
                    "status": item[7],
                }
            )

        conn.close()
        return {"count": len(out), "projects": out}
    elif type == "report":
        r = conn.execute("select *, rowid from reports").fetchall()

        # Form array
        out = []
        for item in r:
            proj = conn.execute(
                text(
                    "select type, author, title, icon, url, description, rowid, status from projects where rowid = :i2"
                ),
                i2=item[2],
            ).fetchone()

            usr = get_user.from_id(item[1])

            author = get_user.from_id(proj[1])

            out.append(
                {
                    "message": item[0],
                    "id": item[3],
                    "reporter": {
                        "username": usr.username,
                        "id": usr.id,
                        "role": usr.role,
                        "bio": usr.bio,
                        "profile_icon": usr.profile_icon,
                    },
                    "project": {
                        "type": proj[0],
                        "author": {
                            "username": author.username,
                            "id": author.id,
                            "role": author.role,
                            "bio": author.bio,
                            "profile_icon": author.profile_icon,
                            "badges": author.badges,
                        },
                        "title": proj[2],
                        "icon": proj[3],
                        "url": proj[4],
                        "description": proj[5],
                        "ID": proj[6],
                        "status": proj[7],
                    },
                }
            )

        conn.close()
        return {"count": len(out), "reports": out}


@mod.route("/project/<int:proj>/action", methods=["PATCH"])
def change_status(proj: int):
    user = auth(
        request.headers.get("Authorization"),
        ["moderator", "admin"],
    )
    if not user:
        return "You can't do this!", 403

    data = request.get_json(force=True)

    try:
        data["action"]
    except KeyError:
        return "action is missing", 400

    conn = create_engine("sqlite://" + config.DATA + "data.db")
    project = conn.execute(
        text(
            "select rowid, status, title, author, description, icon, url from projects where rowid = :pid"
        ),
        pid=proj,
    ).fetchall()

    project = project[0]

    usr = get_user.from_id(project[3])

    if len(project) == 0:
        conn.close()
        return "project not found", 404

    if data["action"] == "publish":
        if project[1] != "live":
            conn.execute(
                text("update projects set status = 'live' where rowid = :pid"), pid=proj
            )
            conn.execute(
                text(
                    "INSERT INTO notifs VALUES (:title, :msg, False, 'default', :uid)"
                ),
                title=f"Published {project[2]}",
                msg=f"Your project, {project[2]}, was published by a staff member.",
                uid=usr.id,
            )
            followers = conn.execute(
                text("select follower from follows where followed = :uid"), uid=usr.id
            ).fetchall()
            for i in followers:
                util.send_notif(
                    conn,
                    f"{usr.username} posted a project!",
                    f"[{usr.username}](https://datapackhub.net/user/{usr.username}) just posted a new project: [{util.clean(project[2])}](https://datapackhub.net/project/{project[6]})",
                    i[0],
                )
            conn.commit()
            conn.close()
            utilities.post.approval(
                user.username,
                project[2],
                project[4],
                project[5],
                project[3],
                project[6],
            )
            return "yep i did the thing", 200
        else:
            return "already live!", 400
    elif data["action"] == "delete":
        conn.execute(
            text("update projects set status = 'deleted' where rowid = :id"), id=proj
        )
        if "message" in data:
            conn.execute(
                text(
                    "INSERT INTO notifs VALUES (:title, :msg, False, 'important', :author)"
                ),
                title=f"Project {project[2]} deleted', msg=f'Your project was deleted for the following reason: {util.clean(data['message'])}",
                author=project[3],
            )
        utilities.post.deletion(
            user.username,
            project[2],
            project[4],
            project[5],
            project[3],
            data["message"],
            project[6],
        )
        conn.commit()
        conn.close()
        return "deleted project"
    elif data["action"] == "restore":
        conn.execute(
            text("update projects set status = 'live' where rowid = :id"), id=proj
        )
        conn.execute(
            text("INSERT INTO notifs VALUES (:title, :msg, False, 'important', :id)"),
            title=f"Project {project[2]} restored",
            msg=f"Your project, {project[2]}, was restored by staff.",
            id=project[3],
        )
        conn.commit()
        conn.close()
        return "restored project"
    elif data["action"] == "disable":
        try:
            data["message"]
        except KeyError:
            return "message is missing, its a disable", 400
        else:
            conn.execute(
                text(
                    "update projects set status = 'disabled', mod_message = :msg where rowid = :id"
                ),
                msg=util.clean(data["message"]),
                id=proj,
            )
            conn.execute(
                text(
                    "INSERT INTO notifs VALUES (:title, :msg, False, 'important', :id)"
                ),
                title=f"Project {project[2]} disabled",
                msg=f"Your project, {project[2]}, was disabled. You need to make changes and then submit it for review. Reason: {util.clean(data['message'])}",
                id=project[3],
            )
            conn.commit()
            conn.close()
            utilities.post.disabled(
                user.username,
                project[2],
                project[4],
                project[5],
                project[3],
                data["message"],
                project[6],
            )
            return "disabled the project lmao xd xd", 200
    elif data["action"] == "write_note":
        try:
            data["message"]
        except KeyError:
            return "message is missing, its a freaking write note action", 400
        else:
            conn.execute(
                text("update projects set mod_message = :msg where rowid = :id"),
                msg=util.clean(data["message"]),
                id=proj,
            )
            conn.execute(
                text(
                    "INSERT INTO notifs VALUES (:title, :msg, False, 'important', :id)"
                ),
                title="New Mod Message",
                msg="A moderator left a message on your project {project[2]}.",
                id=project[3],
            )
            conn.commit()
            conn.close()
            return "Added message", 200
    else:
        return "non existent action lmao xd xd", 400


@mod.route("/project/<int:proj>/dismiss_message", methods=["DELETE"])
def dismiss(proj: int):
    # Authenticate user
    user = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if user == 32:
        return "Please make sure authorization type = Basic", 400
    if user == 33:
        return "Token Expired", 401

    # Get project.
    conn = create_engine("sqlite://" + config.DATA + "data.db")
    project = conn.execute(
        text(
            "select rowid, status, author, mod_message from projects where rowid = :id"
        ),
        id=proj,
    ).fetchall()

    # Check existence of project.
    if len(project) == 0:
        conn.close()
        return "project not found", 404

    project = project[0]

    # Check if user owns project.
    if not (project[2] != user.id or user.role in ["admin", "moderator"]):
        return "You don't own this project!", 403

    # Check status of project
    if project[1] == "disabled":
        return "While the project is disabled, you can't delete the message", 400

    # Delete message
    conn.execute(
        text("update projects set mod_message = null where rowid = :id"), id=id
    )
    conn.commit()
    conn.close()
    return "did it", 200


@mod.route("/remove_report/<int:id>", methods=["delete"])
def remove_report(id: int):
    if not auth(
        request.headers.get("Authorization"),
        ["moderator", "admin"],
    ):
        return "You can't do this!", 403

    conn = create_engine("sqlite://" + config.DATA + "data.db")

    rep = conn.execute(
        text("select rowid from reports where rowid = :id"), id=id
    ).fetchall()
    if len(rep) == 0:
        return "Report not found", 404

    conn.execute(text("delete from reports where rowid = :id"), id=id)
    conn.commit()
    conn.close()

    return "report removed", 200
