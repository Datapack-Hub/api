"""
**Moderation API endpoints**
"""

from flask_cors import CORS
from flask import Blueprint, request
import sqlite3
import config
import json
import difflib
import util
import gen_example_data
import shlex

console_commands = ["sql", "select", "hello", "reset", "notify"]


def auth(token: str, perm_levels: list[str]):
    if not token:
        return False

    user = util.authenticate(token)

    if user == 33:
        return 33

    if user["role"] not in perm_levels:
        return False
    return True


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
            return f"Error: Command {cmd} not found. Did you mean {closest[0]}?", 400
        else:
            return f"Error: Command {cmd} not found.", 400

    # Check user authentication status
    if not util.get_user.from_token(request.headers.get("Authorization")[6:]):
        return "hey u! sign in again plz (i am not hax)", 429

    util.post_site_log(
        util.get_user.from_token(request.headers.get("Authorization")[6:])["username"],
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
            conn = sqlite3.connect(config.DATA + "data.db")
            conn.execute(sql_command)
            conn.commit()
            conn.close()
        except sqlite3.Error as error:
            return "SQL Error: " + (" ".join(error.args)), 400
        else:
            return "Processed SQL command!", 200

    elif cmd == "select":
        if not auth(request.headers.get("Authorization"), ["admin", "developer"]):
            return "You do not have permission to run this command!"

        sql_command = "SELECT " + full[7:]

        # Run SQLITE command
        try:
            print(sql_command)
            conn = sqlite3.connect(config.DATA + "data.db")
            out = conn.execute(sql_command).fetchall()
            conn.commit()
            conn.close()
        except sqlite3.Error as error:
            return "SQL Error: " + (" ".join(error.args)), 400
        else:
            return json.dumps(out, indent=3).replace("\n", "<br />"), 200
    elif cmd == "hello":
        return "Beep boop! Hi!"
    elif cmd == "reset":
        if (
            util.get_user.from_token(request.headers.get("Authorization")[6:])[
                "username"
            ]
            != "Silabear"
        ):
            return "Only Silabear can run this command!", 403
        gen_example_data.reset(args[0])
        return "Reset the database."
    elif cmd == "notify":
        if not auth(
            request.headers.get("Authorization"),
            ["admin", "developer", "moderator", "helper"],
        ):
            return "You can't run this command!", 403
        if len(args) < 3:
            return "Missing values!", 400
        conn = sqlite3.connect(config.DATA + "data.db")
        try:
            conn.execute(
                f"INSERT INTO notifs VALUES ('{args[1]}', '{args[2]}', False, {args[0]}, '{args[3]}')"
            )
        except sqlite3.Error as er:
            return "Error: " + " ".join(er.args), 400
        conn.commit()
        conn.close()
        return "Notified the user!"


@mod.route("/get_members")
def members():
    # Check auth
    if not auth(request.headers.get("Authorization"), ["admin"]):
        return 403

    conn = sqlite3.connect(config.DATA + "data.db")

    data = conn.execute(
        "SELECT rowid, username, profile_icon, role, github_id FROM users"
    ).fetchall()

    return_this = ""

    for i in data:
        return_this = (
            return_this
            + f"""<tr>
        <th scope="row">{i[0]}</th>
        <td><img class="smol" src="{i[2]}" />{i[1]}</td>
        <td>{i[3].capitalize()}</td>
        <td>{i[4]}</td>
        <td>
            <button self="logout" type="button" class="btn btn-danger btn-sm" onclick="logOutButton({i[0]})">Log Out</button>
            <button self="ban" type="button" class="btn btn-danger btn-sm" onclick="banButton({i[0]})">Ban</button>
        </td></tr>"""
        )

        print(return_this)

    return {"result": return_this}


@mod.route("/log_out/<int:self>", methods=["post"])
def logout():
    # Check auth
    if not auth(
        request.headers.get("Authorization"), ["admin", "moderator", "developer"]
    ):
        return 403

    try:
        util.log_user_out(id)
    except:
        return "Failed", 500
    else:
        util.post_site_log(
            util.get_user.from_token(request.headers.get("Authorization")[6:])[
                "username"
            ],
            "Logged user out",
            f"Logged out user`{id}`",
        )
        return "Success!", 200


@mod.route("/ban/<int:self>", methods=["post", "delete"])
def ban():
    if not auth(
        request.headers.get("Authorization"), ["admin", "moderator", "developer"]
    ):
        return "Not allowed.", 403
    if request.method == "POST":
        dat = request.get_json(force=True)

        conn = sqlite3.connect(config.DATA + "data.db")
        try:
            conn.execute(
                f"insert into banned_users values ({dat['self']}, {dat['expires']}, '{util.sanitise(dat['message'])}')"
            )
        except sqlite3.Error as er:
            return " ".join(er.args)
        else:
            conn.commit()
            conn.close()
            util.post_site_log(
                util.get_user.from_token(request.headers.get("Authorization")[6:])[
                    "username"
                ],
                "Banned User",
                f"Banned user `{util.get_user.from_id(id)}` for reason `{dat['message']}`",
            )
            return "worked fine"
    else:
        dat = request.get_json(force=True)
        conn = sqlite3.connect(config.DATA + "data.db")
        try:
            conn.execute(f"delete from banned_users where self = {id}")
        except sqlite3.Error as er:
            return " ".join(er.args)
        else:
            conn.commit()
            conn.close()
            util.post_site_log(
                util.get_user.from_token(request.headers.get("Authorization")[6:])[
                    "username"
                ],
                "Banned User",
                f"Banned user `{util.get_user.from_id(id)}` for reason `{dat['message']}`",
            )
            return "worked fine"


@mod.route("/user/<int:id>")
def user_data(id):
    if not auth(
        request.headers.get("Authorization"), ["moderator", "developer", "admin"]
    ):
        return "You can't do this!", 403

    conn = sqlite3.connect(config.DATA + "data.db")
    ban_data = conn.execute(f"SELECT * FROM banned_users WHERE id = {id}").fetchall()

    if len(ban_data) == 0:
        return {"banned": False, "banMessage": None, "banExpiry": None}
    else:
        return {
            "banned": True,
            "banMessage": ban_data[0][2],
            "banExpiry": ban_data[0][1],
        }


@mod.route("/logs")
def logs():
    if not auth(
        request.headers.get("Authorization"),
        ["helper", "moderator", "developer", "admin"],
    ):
        return "You can't do this!", 403

    page = request.args.get("page", 1)

    conn = sqlite3.connect(config.DATA + "data.db")
    x = conn.execute("select username, action, time from mod_logs").fetchall()
    if int(page) > 1:
        x = x[((int(page) - 1) * 30) - 1 : ((int(page)) * 30) - 1]
    else:
        x = x[0:29]
    y = []
    for i in x:
        y.append({"username": i[0], "action": i[1], "time": i[2]})

    return {"result": y}


@mod.route("/queue/<string:type>")
def queue(type: str):
    if not auth(
        request.headers.get("Authorization"),
        ["moderator", "admin"],
    ):
        return "You can't do this!", 403

    conn = sqlite3.connect(config.DATA + "data.db")

    if type == "publish":
        r = conn.execute(
            "select type, author, title, icon, url, description, rowid, status from projects where status = 'publish_queue'"
        ).fetchall()

        # Form array
        out = []
        for item in r:
            out.append(
                {
                    "type": item[0],
                    "author": item[1],
                    "title": item[2],
                    "icon": item[3],
                    "url": item[4],
                    "description": item[5],
                    "ID": item[6],
                    "status": item[7],
                }
            )
    elif type == "review":
        r = conn.execute(
            "select type, author, title, icon, url, description, rowid, status from projects where status = 'review_queue'"
        ).fetchall()

        # Form array
        out = []
        for item in r:
            out.append(
                {
                    "type": item[0],
                    "author": item[1],
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


@mod.route("/project/<int:proj>/action", methods=["PATCH"])
def change_status(proj: int):
    if not auth(
        request.headers.get("Authorization"),
        ["moderator", "admin"],
    ):
        return "You can't do this!", 403

    data = request.get_json(force=True)

    try:
        data["action"]
    except:
        return "action is missing", 400

    conn = sqlite3.connect(config.DATA + "data.db")
    project = conn.execute(
        "select rowid, status from projects where rowid = " + str(proj)
    ).fetchall()

    if len(project) == 0:
        conn.close()
        return "project not found", 404

    if data["action"] == "publish":
        conn.execute("update projects set status = 'live' where rowid = " + str(proj))
        conn.commit()
        conn.close()
        return "yep i did the thing", 200
    elif data["action"] == "delete":
        pass
    elif data["action"] == "disable":
        try:
            data["message"]
        except:
            return "message is missing, its a disable", 400
        else:
            pass
        pass
    elif data["action"] == "write_note":
        try:
            data["message"]
        except:
            return "message is missing, its a freaking write note action", 400
        else:
            conn.execute(f"update projects set mod_message = '{util.sanitise(data['message'])}' where rowid = {str(proj)}")
            conn.commit()
            conn.close()
            return "Added message", 200
    else:
        return "non existent action lmao xd xd", 400

    return "uh", 500

@mod.route("/project/<int:proj>/dismiss_message", methods=["DELETE"])
def dismiss(proj: int):
    # Authenticate user
    user = util.authenticate(request.headers.get("Authorization"))
    if user == 32:
        return "Please make sure authorization type = Basic"
    if user == 33:
        return "Token Expired", 498
    
    # Get project.
    conn = sqlite3.connect(config.DATA + "data.db")
    project = conn.execute(
        "select rowid, status, author, mod_message from projects where rowid = " + str(proj)
    ).fetchall()

    # Check existence of project.
    if len(project) == 0:
        conn.close()
        return "project not found", 404
    
    project = project[0]
    
    # Check if user owns project.
    if project[2] != user["id"]:
        return "You don't own this project!", 403
    
    # Check status of project
    if project[1] == "disabled":
        return "While the project is disabled, you can't delete the message", 400
    
    # Delete message
    conn.execute("update projects set mod_message = null where rowid = " + str(proj))
    conn.commit()
    conn.close()
    return "did it", 200