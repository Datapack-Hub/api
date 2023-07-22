"""
**User API endpoints**
"""

import json
import sqlite3
import time
import traceback

from flask import Blueprint, request

import config
import utilities.auth_utils
import utilities.get_user
import utilities.post
import utilities.util as util
from routes.moderation import auth

ADMINS = ["Silabear", "Flynecraft", "HoodieRocks"]
user = Blueprint("user", __name__, url_prefix="/user")

# CORS(user)


# @user.after_request
# def after(resp):
#     resp.headers.add("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
#     return resp


@user.route("/badges/<int:id>", methods=["PATCH", "GET"])
def badges(id: int):
    conn = sqlite3.connect(config.DATA + "data.db")

    if request.method == "GET":
        return {"badges": utilities.get_user.from_id(id).badges}
    if request.method == "PATCH":
        if not auth(
            request.headers.get("Authorization"), ["moderator", "developer", "admin"]
        ):
            return "You can't do this!", 403

        try:
            body = request.get_json(force=True)
        except KeyError:
            return "Malformed request", 400

        try:
            badge_str = str(body["badges"]).replace("'", '"')

            print(badge_str)

            conn.execute(
                f"""UPDATE users 
                    SET badges = '{badge_str}'
                    WHERE rowid = {id}"""
            )
        except sqlite3.Error:
            print(traceback.print_exc())
            conn.rollback()
            conn.close()
            return "Database Error", 500
        else:
            conn.commit()
            conn.close()
            return "Success!"


@user.route("/staff/<role>")
def staff(role):
    conn = sqlite3.connect(config.DATA + "data.db")
    if role == "default":
        return "Role has to be staff role", 400
    list = conn.execute(
        f"select username, rowid, bio, profile_icon from users where role = '{util.clean(role)}'"
    ).fetchall()
    finale = []
    for i in list:
        finale.append(
            {
                "id": i[1],
                "username": i[0],
                "role": role,
                "bio": i[2],
                "profile_icon": i[3],
            }
        )
    return {"count": len(finale), "values": finale}


@user.route("/staff/roles")
def roles():
    return json.load(open(config.DATA + "roles.json", "r+"))


@user.route("/<string:username>", methods=["GET", "PATCH"])
def get_user(username):
    # TODO mods can see banned users
    u = utilities.get_user.from_username(username)
    if not u:
        return "User does not exist", 404
    return {
        "username": u.username,
        "id": u.id,
        "role": u.role,
        "bio": u.bio,
        "profile_icon": u.profile_icon,
        "badges": u.badges,
    }


@user.route("/id/<int:id>", methods=["GET", "PATCH"])
def get_user_id(id):
    # TODO mods can see banned users
    if request.method == "GET":
        u = utilities.get_user.from_id(id)
        if not u:
            return "User does not exist", 404
        return {
            "username": u.username,
            "id": u.id,
            "role": u.role,
            "bio": u.bio,
            "profile_icon": u.profile_icon,
            "badges": u.badges,
        }
    elif request.method == "PATCH":
        dat = request.get_json(force=True)

        usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
        if usr == 32:
            return "Please make sure authorization type = Basic", 400
        if usr == 33:
            return "Token Expired", 401

        banned = util.get_user_ban_data(usr.id)
        if banned is not None:
            return {
                "banned": True,
                "reason": banned["reason"],
                "expires": banned["expires"],
            }, 403

        if not (usr.id == id or usr.role in ["moderator", "admin"]):
            return "You aren't allowed to edit this user!", 403

        if len(dat["username"]) > 32:
            return "Username too long", 400
        if len(dat["bio"]) > 500:
            return "Bio too long", 400

        conn = sqlite3.connect(config.DATA + "data.db")
        try:
            conn.execute(
                f"UPDATE users SET username = '{util.clean(dat['username'])}' where rowid = {id}"
            )
            conn.execute(
                f"UPDATE users SET bio = '{util.clean(dat['bio'])}' where rowid = {id}"
            )
            if usr.role == "admin":
                conn.execute(
                    f"UPDATE users SET role = '{util.clean(dat['role'])}' where rowid = {id}"
                )
                utilities.post.site_log(
                    usr.username,
                    "Edited user",
                    f"Edited user data of {dat['username']}",
                )
        except sqlite3.Error:
            return "Something went a little bit wrong"
        conn.commit()
        conn.close()
        return "done!"


@user.route("/me")
def me():
    if not request.headers.get("Authorization"):
        return "Authorization required", 401

    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic", 400
    if usr == 33:
        return "Token Expired", 401

    # User Data
    userdata = {
        "username": usr.username,
        "id": usr.id,
        "role": usr.role,
        "bio": usr.bio,
        "profile_icon": usr.profile_icon,
    }

    # banned?
    conn = sqlite3.connect(config.DATA + "data.db")
    x = conn.execute(
        "SELECT rowid, expires, reason from banned_users where id = " + str(usr.id)
    ).fetchall()
    if len(x) == 1:
        current = int(time.time())
        expires = x[0][1]
        if current > expires:
            conn.execute(f"delete from banned_users where rowid = {str(x[0][0])}")
            conn.commit()
        else:
            userdata["banned"] = True
            userdata["banData"] = {"message": x[0][2], "expires": expires}
    else:
        userdata["banned"] = False

    # failsafe
    if usr.username in ADMINS:
        conn.execute(
            f"update users set role = 'admin' where username = '{util.clean(usr.username)}'"
        )
        conn.commit()
    conn.close()
    return userdata


@user.route("/<string:username>/projects")
def user_projects(username):
    conn = sqlite3.connect(config.DATA + "data.db")

    # Check if user is authenticated
    t = request.headers.get("Authorization")
    user = utilities.get_user.from_username(username)
    authed = utilities.auth_utils.authenticate(t)
    if authed == 32:
        return "Make sure authorization is basic!", 400
    elif authed == 33:
        return "Token expired!", 401

    if t:
        if authed.id == user.id:
            # Get all submissions
            r = conn.execute(
                f"select type, author, title, icon, url, description, rowid, status, downloads from projects where author = {user.id} and status != 'deleted'"
            ).fetchall()

            # Form array
            out = []
            for item in r:
                latest_version = conn.execute(
                    f"SELECT * FROM versions WHERE project = {item[6]} ORDER BY rowid DESC"
                ).fetchall()

                temp = {
                    "type": item[0],
                    "author": {
                        "username": user.username,
                        "id": user.id,
                        "role": user.role,
                        "bio": user.bio,
                        "profile_icon": user.profile_icon,
                        "badges": user.badges,
                    },
                    "title": item[2],
                    "icon": item[3],
                    "url": item[4],
                    "description": item[5],
                    "ID": item[6],
                    "status": item[7],
                    "downloads": item[8],
                }

                if len(latest_version) != 0:
                    temp["latest_version"] = {
                        "name": latest_version[0][0],
                        "description": latest_version[0][1],
                        "minecraft_versions": latest_version[0][4],
                        "version_code": latest_version[0][5],
                    }

                out.append(temp)

            conn.close()

            return {"count": len(out), "result": out}
        else:
            # Get all PUBLIC submissions
            r = conn.execute(
                f"select type, author, title, icon, url, description, rowid, status, downloads from projects where author = {user.id} and status == 'live'"
            ).fetchall()

            # Form array
            out = []
            for item in r:
                out.append(
                    {
                        "type": item[0],
                        "author": {
                            "username": user.username,
                            "id": user.id,
                            "role": user.role,
                            "bio": user.bio,
                            "profile_icon": user.profile_icon,
                            "badges": user.badges,
                        },
                        "title": item[2],
                        "icon": item[3],
                        "url": item[4],
                        "description": item[5],
                        "ID": item[6],
                        "status": item[7],
                        "downloads": item[8],
                    }
                )

            conn.close()

            return {"count": len(out), "result": out}
    else:
        # Get all PUBLIC submissions
        r = conn.execute(
            f"select type, author, title, icon, url, description, rowid from projects where author = {user.id} and status == 'live'"
        ).fetchall()

        # Form array
        out = []
        for item in r:
            out.append(
                {
                    "type": item[0],
                    "author": {
                        "username": user.username,
                        "id": user.id,
                        "role": user.role,
                        "bio": user.bio,
                        "profile_icon": user.profile_icon,
                        "badges": user.badges,
                    },
                    "title": item[2],
                    "icon": item[3],
                    "url": item[4],
                    "description": item[5],
                    "ID": item[6],
                }
            )

        conn.close()

        return {"count": len(out), "result": out}
