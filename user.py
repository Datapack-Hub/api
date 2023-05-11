"""
**User API endpoints**
"""


from flask import Blueprint, request
import sqlite3

from flask_cors import CORS
import config
import time
import json

import util

ADMINS = ["Silabear", "Flynecraft", "HoodieRocks"]
user = Blueprint("user", __name__, url_prefix="/user")

CORS(user)

# @user.after_request
# def after(resp):
#     resp.headers.add("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
#     return resp


@user.route("/staff/<role>")
def staff(role):
    conn = sqlite3.connect(config.DATA + "data.db")
    if role == "default":
        return "Role has to be staff role", 400
    list = conn.execute(
        f"select username, rowid, role, bio, profile_icon from users where role = '{role}'"
    ).fetchall()
    finale = []
    for i in list:
        finale.append(
            {
                "id": i[1],
                "username": i[0],
                "role": i[2],
                "bio": i[3],
                "profile_icon": i[4],
            }
        )
    return {"count": len(finale), "values": finale}


@user.route("/staff/roles")
def roles():
    return json.load(open(config.DATA + "roles.json", "r+"))


@user.route("/<string:username>", methods=["GET", "PATCH"])
def get_user(username):
    # TODO mods can see banned users
    start_time = time.time()
    u = util.get_user.from_username(username)
    if not u:
        return "User does not exist", 404
    print("%s to run" % start_time - time.time())
    return u


@user.route("/id/<int:id>", methods=["GET", "PATCH"])
def get_user_id(id):
    # TODO mods can see banned users
    if request.method == "GET":
        u = util.get_user.from_id(id)
        if not u:
            return "User does not exist", 404
        return u
    elif request.method == "PATCH":
        dat = request.get_json(force=True)

        usr = util.authenticate(request.headers.get("Authorization"))
        if usr == 32:
            return "Please make sure authorization type = Basic"
        if usr == 33:
            return "Token Expired", 498

        banned = util.get_user_ban_data(usr["id"])
        if banned is not None:
            return {
                "banned": True,
                "reason": banned["reason"],
                "expires": banned["expires"],
            }, 403

        if not (usr["id"] == id or usr["role"] in ["moderator", "admin"]):
            return "You aren't allowed to edit this user!", 403

        if len(dat["username"]) > 32:
            return "Username too long", 400
        if len(dat["bio"]) > 500:
            return "Bio too long", 400

        conn = sqlite3.connect(config.DATA + "data.db")
        try:
            conn.execute(
                f"UPDATE users SET username = '{dat['username']}' where rowid = {id}"
            )
            conn.execute(f"UPDATE users SET bio = '{dat['bio']}' where rowid = {id}")
            if usr["role"] == "admin":
                conn.execute(
                    f"UPDATE users SET role = '{dat['role']}' where rowid = {id}"
                )
                util.post_site_log(
                    usr["username"],
                    "Edited user",
                    f"Edited user data of {dat['username']}",
                )
        except sqlite3.Error:
            return "Something went a little bit wrong"
        conn.commit()
        conn.close()
        return util.get_user.from_id(id)


@user.route("/me")
def me():
    # TODO user can see if they are banned
    if not request.headers.get("Authorization"):
        return "Authorization required", 401

    usr = util.authenticate(request.headers.get("Authorization"))

    if usr == 32:
        return "Please make sure authorization type = Basic"

    if usr == 33:
        return "Token Expired", 498

    # banned?
    conn = sqlite3.connect(config.DATA + "data.db")
    x = conn.execute(
        "SELECT rowid, expires, reason from banned_users where id = " + str(usr["id"])
    ).fetchall()
    if len(x) == 1:
        current = int(time.time())
        expires = x[0][1]
        if current > expires:
            conn.execute(f"delete from banned_users where rowid = {str(x[0][0])}")
            conn.commit()
        else:
            usr["banned"] = True
            usr["banData"] = {"message": x[0][2], "expires": expires}
    else:
        usr["banned"] = False

    # failsafe
    if usr["username"] in ADMINS:
        conn.execute(
            f"update users set role = 'admin' where username = '{usr['username']}'"
        )
        conn.commit()
    conn.close()
    return usr


@user.route("/<string:username>/projects")
def user_projects(username):
    conn = sqlite3.connect(config.DATA + "data.db")
    # Check if user is authenticated
    t = request.headers.get("Authorization")
    user = util.get_user.from_username(username)

    authed = util.authenticate(t)

    if authed == 32:
        return "Make sure authorization is basic!", 400
    elif authed == 33:
        return "Token expired!", 429

    if t:
        if authed["id"] == user["id"]:
            # Get all submissions
            r = conn.execute(
                f"select type, author, title, icon, url, description, rowid, status from projects where author = {user['id']} and status != 'deleted'"
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

            return {"count": len(out), "result": out}
        else:
            # Get all PUBLIC submissions
            r = conn.execute(
                f"select type, author, title, icon, url, description, rowid, status from projects where author = {user['id']} and status == 'live'"
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

            return {"count": len(out), "result": out}
    else:
        # Get all PUBLIC submissions
        r = conn.execute(
            f"select type, author, title, icon, url, description, rowid from projects where author = {user['id']} and status == 'live'"
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
                }
            )

        conn.close()

        return {"count": len(out), "result": out}
