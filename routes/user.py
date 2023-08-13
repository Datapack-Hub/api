"""
**User API endpoints**
"""

import json
import sqlite3
import time
import traceback

from flask import Blueprint, request
from sqlalchemy import create_engine, text

import config
import utilities.auth_utils
import utilities.get_user
import utilities.post
import utilities.util as util
from routes.moderation import auth
from routes.projects import parse_project

ADMINS = ["Silabear", "Flynecraft", "HoodieRocks"]
user = Blueprint("user", __name__, url_prefix="/user")

# CORS(user)


# @user.after_request
# def after(resp):
#     resp.headers.add("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
#     return resp


@user.route("/badges/<int:id>", methods=["PATCH", "GET"])
def badges(id: int):
    conn = create_engine(config.DATA + "data.db")

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
                text(
                    """UPDATE users 
                    SET badges = :badges
                    WHERE rowid = :id"""
                ),
                badges=badge_str,
                id=id,
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
    conn = create_engine(config.DATA + "data.db")
    if not role in ["admin", "moderator", "helper"]:
        return "Role has to be staff role", 400
    list = conn.execute(
        text("select username, rowid, bio, profile_icon from users where role = :role"),
        role=util.clean(role),
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


@user.route("/<string:username>", methods=["GET"])
def get_user(username):
    # TODO mods can see banned users
    u = utilities.get_user.from_username(username)
    if not u:
        return "User does not exist", 404

    return_data = {
        "username": u.username,
        "id": u.id,
        "role": u.role,
        "bio": u.bio,
        "profile_icon": u.profile_icon,
        "badges": u.badges,
    }

    if request.headers.get("Authorization"):
        usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
        if usr == 32:
            return "Please make sure authorization type = Basic", 400
        if usr == 33:
            return "Token Expired", 401

        conn = create_engine(config.DATA + "data.db")
        followed = conn.execute(
            text("select * from follows where follower = :fid and followed = :uid;"),
            fid=u.id,
            uid=usr.id,
        ).fetchall()
        if len(followed) == 0:
            return_data["followed"] = False
        else:
            return_data["followed"] = True

    return return_data


@user.route("/id/<int:id>", methods=["GET", "PATCH"])
def get_user_id(id):
    # TODO mods can see banned users
    if request.method == "GET":
        u = utilities.get_user.from_id(id)
        if not u:
            return "User does not exist", 404

        return_data = {
            "username": u.username,
            "id": u.id,
            "role": u.role,
            "bio": u.bio,
            "profile_icon": u.profile_icon,
            "badges": u.badges,
        }

        if request.headers.get("Authorization"):
            usr = utilities.auth_utils.authenticate(
                request.headers.get("Authorization")
            )
            if usr == 32:
                return "Please make sure authorization type = Basic", 400
            if usr == 33:
                return "Token Expired", 401

            conn = create_engine(config.DATA + "data.db")
            followed = conn.execute(
                text(
                    "select * from follows where follower = :fid and followed = :uid;"
                ),
                fid=u.id,
                uid=usr.id,
            ).fetchall()
            if len(followed) == 0:
                return_data["followed"] = False
            else:
                return_data["followed"] = True

        return return_data
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

        conn = create_engine(config.DATA + "data.db")
        try:
            conn.execute(
                text("UPDATE users SET username = :name where rowid = :id"),
                name=util.clean(dat["username"]),
                id=id,
            )
            conn.execute(
                text("UPDATE users SET bio = ':bio where rowid = :id"),
                bio=util.clean(dat["bio"]),
                id=id,
            )
            if usr.role == "admin":
                conn.execute(
                    text("UPDATE users SET role = :role where rowid = :id"),
                    role=util.clean(dat["role"]),
                    id=id,
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
    user_data = {
        "username": usr.username,
        "id": usr.id,
        "role": usr.role,
        "bio": usr.bio,
        "profile_icon": usr.profile_icon,
    }

    # banned?
    conn = create_engine(config.DATA + "data.db")
    x = conn.execute(
        text("SELECT rowid, expires, reason from banned_users where id = :id"),
        id=usr.id,
    ).fetchall()
    if len(x) == 1:
        current = int(time.time())
        expires = x[0][1]
        if current > expires:
            conn.execute(text("delete from banned_users where rowid = :id"), id=x[0][0])
            conn.commit()
        else:
            user_data["banned"] = True
            user_data["banData"] = {"message": x[0][2], "expires": expires}
    else:
        user_data["banned"] = False

    # fail safe
    if usr.username in ADMINS:
        conn.execute(
            text("update users set role = 'admin' where username = :uname"),
            uname=util.clean(usr.username),
        )
        conn.commit()
    conn.close()
    return user_data


@user.route("/<string:username>/projects")
def user_projects(username):
    conn = create_engine(config.DATA + "data.db")

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
                text(
                    "select rowid, * from projects where author = :id and status != 'deleted'"
                ),
                id=user.id,
            ).fetchall()

            # Form array
            out = []
            for item in r:
                try:
                    temp = parse_project(item, conn)
                except:
                    conn.rollback()
                    conn.close()
                    return "Something bad happened", 500

                out.append(temp)

            conn.close()

            return {"count": len(out), "result": out}
        else:
            # Get all PUBLIC submissions
            r = conn.execute(
                text(
                    "select rowid, * from projects where author = :id and status = 'live'"
                ),
                id=user.id,
            ).fetchall()

            # Form array
            out = []
            for item in r:
                try:
                    temp = parse_project(item, conn)
                except:
                    conn.rollback()
                    conn.close()
                    return "Something bad happened", 500

                out.append(temp)

            conn.close()

            return {"count": len(out), "result": out}
    else:
        # Get all PUBLIC submissions
        r = conn.execute(
            text(
                "select rowid, * from projects where author = :id and status = 'live'"
            ),
            id=user.id,
        ).fetchall()

        # Form array
        out = []
        for item in r:
            try:
                temp = parse_project(item, conn)
            except:
                conn.rollback()
                conn.close()
                return "Something bad happened", 500

            out.append(temp)

        conn.close()

        return {"count": len(out), "result": out}


@user.route("/id/<int:id>/follow", methods=["POST"])
def follow(id):
    if not request.headers.get("Authorization"):
        return "Authorization required", 401

    follower = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if follower == 32:
        return "Please make sure authorization type = Basic", 400
    if follower == 33:
        return "Token Expired", 401

    followed = utilities.get_user.from_id(id)
    if not followed:
        return "User doesn't exist.", 404

    conn = create_engine(config.DATA + "data.db")
    fol = conn.execute(
        text("select * from follows where follower = :fid and followed = :fid;"),
        fid=follower.id,
    ).fetchall()
    if len(fol) == 0:
        try:
            conn.execute(
                text("insert into follows values (:follower, :followed);"),
                follower=follower.id,
                followed=followed.id,
            )
        except:
            conn.rollback()
            conn.close()
            return "Something went wrong.", 500
        else:
            conn.execute(
                text(
                    "INSERT INTO notifs VALUES (:title, :msg, False, 'default', :fid)"
                ),
                title="New follower",
                msg=f"[{follower.username}](https://datapackhub.net/user/{follower.username}) followed you!",
                fid=followed.id,
            )
            conn.commit()
            conn.close()
            return "Followed user!", 200
    else:
        try:
            conn.execute(
                text(
                    "delete from follows where follower = :follower and followed = :followed;"
                ),
                follower=follower.id,
                followed=followed.id,
            )
        except:
            conn.rollback()
            conn.close()
            return "Something went wrong.", 500
        else:
            conn.commit()
            conn.close()
            return "Unfollowed user!", 200
