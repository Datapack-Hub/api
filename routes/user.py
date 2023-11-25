"""
**User API endpoints**
"""

import json
import sqlite3
import time
import traceback
from pathlib import Path

from flask import Blueprint, request

import config
import utilities.auth_utils as auth_util
import utilities.get_user
import utilities.weblogs
from routes.moderation import is_perm_level
from routes.projects import parse_project
from utilities import util

ADMINS = ["Silabear", "Flynecraft", "HoodieRocks"]
user = Blueprint("user", __name__, url_prefix="/user")


# @user.after_request
# def after(resp):


@user.route("/badges/<int:id>", methods=["PATCH", "GET"])
def user_badges_by_id(id: int):
    conn = util.make_connection()

    if request.method == "GET":
        return {"badges": utilities.get_user.from_id(id).badges}
    if request.method == "PATCH":
        if not is_perm_level(
            request.headers.get("Authorization"), ["moderator", "developer", "admin"]
        ):
            return "You can't do this!", 403

        try:
            body = request.get_json(force=True)
        except KeyError:
            return "Malformed request", 400

        try:
            badge_str = str(body["badges"]).replace("'", '"')

            util.log(badge_str)

            util.exec_query(
                conn,
                """UPDATE users 
                    SET badges = :badges
                    WHERE rowid = :id""",
                badges=badge_str,
                id=id,
            )
        except sqlite3.Error:
            util.weblogs.error("Whoopsie!", traceback.print_exc())
            conn.rollback()

            return "Database Error", 500
        else:
            conn.commit()

            return "Success!"


@user.route("/staff/<role>")
def get_staff_role(role):
    conn = util.make_connection()
    if role not in ["admin", "moderator", "helper"]:
        return "Role has to be staff role", 400
    list = util.exec_query(
        conn,
        "select username, rowid, bio, profile_icon from users where role = :role",
        role=role,
    ).all()
    finale = [
        {
            "id": i[1],
            "username": i[0],
            "role": role,
            "bio": i[2],
            "profile_icon": i[3],
        }
        for i in list
    ]
    return {"count": len(finale), "values": finale}


@user.route("/staff/roles")
def get_all_roles():
    return json.load(Path(config.DATA + "roles.json").open("r+"))


@user.route("/<string:username>", methods=["GET"])
def get_by_username(username):
    # TODO: mods can see banned users
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
        "join_date": u.join_date * 1000,
    }

    if request.headers.get("Authorization"):
        usr = auth_util.authenticate(request.headers.get("Authorization"))
        if usr == 32:
            return "Please make sure authorization type = Basic", 400
        if usr == 33:
            return "Token Expired", 401

        conn = util.make_connection()
        followed = util.exec_query(
            conn,
            "select * from follows where follower = :fid and followed = :uid;",
            fid=u.id,
            uid=usr.id,
        ).all()
        if not followed:
            return_data["followed"] = False
        else:
            return_data["followed"] = True

    return return_data


@user.route("/id/<int:id>", methods=["GET", "PATCH"])
def user_by_id(id):
    # TODO: mods can see banned users
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
            "join_date": u.join_date * 1000,
        }

        if request.headers.get("Authorization"):
            usr = auth_util.authenticate(request.headers.get("Authorization"))
            if usr == 32:
                return "Please make sure authorization type = Basic", 400
            if usr == 33:
                return "Token Expired", 401

            conn = util.make_connection()
            followed = util.exec_query(
                conn,
                "select * from follows where follower = :fid and followed = :uid;",
                fid=u.id,
                uid=usr.id,
            ).all()
            if not followed:
                return_data["followed"] = False
            else:
                return_data["followed"] = True

        return return_data
    elif request.method == "PATCH":
        dat = request.get_json(force=True)

        usr = auth_util.authenticate(request.headers.get("Authorization"))
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

        conn = util.make_connection()
        try:
            util.exec_query(
                conn,
                "UPDATE users SET username = :name where rowid = :id",
                name=dat["username"],
                id=id,
            )
            util.exec_query(
                conn,
                "UPDATE users SET bio = :bio where rowid = :id",
                bio=dat["bio"],
                id=id,
            )
            if usr.role == "admin":
                util.exec_query(
                    conn,
                    "UPDATE users SET role = :role where rowid = :id",
                    role=dat["role"],
                    id=id,
                )
                utilities.weblogs.site_log(
                    usr.username,
                    "Edited user",
                    f"Edited user data of {dat['username']}",
                )
        except sqlite3.Error:
            conn.rollback()

            return "Something went a little bit wrong"
        conn.commit()

        return "done!"


@user.route("/me")
def get_self():
    if not request.headers.get("Authorization"):
        return "Authorization required", 401

    usr = auth_util.authenticate(request.headers.get("Authorization"))
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
        "join_date": usr.join_date * 1000,
    }

    # banned?
    conn = util.make_connection()
    x = util.exec_query(
        conn,
        "SELECT rowid, expires, reason from banned_users where id = :id",
        id=usr.id,
    ).all()
    if len(x) == 1:
        current = int(time.time())
        expires = x[0][1]
        if current > expires:
            util.exec_query(
                conn, "delete from banned_users where rowid = :id", id=x[0][0]
            )
            conn.commit()
        else:
            user_data["banned"] = True
            user_data["banData"] = {"message": x[0][2], "expires": expires}
    else:
        user_data["banned"] = False

    # fail safe
    if usr.username in ADMINS:
        util.exec_query(
            conn,
            "update users set role = 'admin' where username = :uname",
            uname=usr.username,
        )
        conn.commit()

    return user_data


@user.route("/me/log_out")
def log_out_self():
    if not request.headers.get("Authorization"):
        return "You can't log yourself out if you're not logged in", 400

    usr = auth_util.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic", 400
    if usr == 33:
        return (
            "Your token expired or you're already logged out, we don't know at this point",
            401,
        )

    auth_util.log_user_out(usr.id)
    return "Successfully signed out!"


@user.route("/<string:username>/projects")
def get_user_projects(username: str):
    conn = util.make_connection()

    # Check if user is authenticated
    t = request.headers.get("Authorization")
    user = utilities.get_user.from_username(username)
    
    authed = auth_util.authenticate(t)
    if authed == 32:
        return "Make sure authorization is basic!", 400
    elif authed == 33:
        return "Token expired!", 401

    if user is None:
        return "User not found", 404

    if t:
        if authed.id == user.id:
            # Get all submissions
            r = util.exec_query(
                conn,
                "select rowid, * from projects where author = :id and status != 'deleted'",
                id=user.id,
            ).all()

            # Form array
            out = []
            for item in r:
                try:
                    temp = parse_project(item, conn)
                except:
                    conn.rollback()

                    return "Something bad happened", 500

                out.append(temp)

            return {"count": len(out), "result": out}
        else:
            # Get all PUBLIC submissions
            r = util.exec_query(
                conn,
                "select rowid, * from projects where author = :id and status = 'live'",
                id=user.id,
            ).all()

            # Form array
            out = []
            for item in r:
                try:
                    temp = parse_project(item, conn)
                except:
                    conn.rollback()

                    return "Something bad happened", 500

                out.append(temp)

            return {"count": len(out), "result": out}
    else:
        # Get all PUBLIC submissions
        r = util.exec_query(
            conn,
            "select rowid, * from projects where author = :id and status = 'live'",
            id=user.id,
        ).all()

        # Form array
        out = []
        for item in r:
            try:
                temp = parse_project(item, conn)
            except:
                conn.rollback()

                return "Something bad happened", 500

            out.append(temp)

        return {"count": len(out), "result": out}


@user.route("/id/<int:id>/follow", methods=["POST"])
def follow_user(id):
    if not request.headers.get("Authorization"):
        return "Authorization required", 401

    follower = auth_util.authenticate(request.headers.get("Authorization"))
    if follower == 32:
        return "Please make sure authorization type = Basic", 400
    if follower == 33:
        return "Token Expired", 401

    followed = utilities.get_user.from_id(id)
    if not followed:
        return "User doesn't exist.", 404

    if followed.id == follower.id:
        return "You can't follow yourself, silly!", 400

    conn = util.make_connection()
    fol = util.exec_query(
        conn,
        "select * from follows where follower = :fid and followed = :fid;",
        fid=follower.id,
    ).all()
    if not fol:
        try:
            util.exec_query(
                conn,
                "insert into follows values (:follower, :followed);",
                follower=follower.id,
                followed=followed.id,
            )
        except:
            conn.rollback()

            return "Something went wrong.", 500
        else:
            util.exec_query(
                conn,
                "INSERT INTO notifs VALUES (:title, :msg, False, 'default', :fid)",
                title="New follower",
                msg=f"[{follower.username}](https://datapackhub.net/user/{follower.username}) followed you!",
                fid=followed.id,
            )
            conn.commit()

            return "Followed user!", 200
    else:
        try:
            util.exec_query(
                conn,
                "delete from follows where follower = :follower and followed = :followed;",
                follower=follower.id,
                followed=followed.id,
            )
        except:
            conn.rollback()

            return "Something went wrong.", 500
        else:
            conn.commit()

            return "Unfollowed user!", 200
