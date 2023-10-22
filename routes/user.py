"""
**User API endpoints**
"""

import json
import sqlite3
import time
import traceback
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

import config
from utilities.request_types import BadgesJsonBody, UserEditBody
import utilities.auth_utils as auth_util
import utilities.get_user
import utilities.weblogs
from routes.moderation import is_perm_level
from routes.projects import parse_project
from utilities import util

ADMINS = ["Silabear", "Flynecraft", "HoodieRocks"]
user = APIRouter(prefix="/user", tags=["users"])

@user.get("/badges/{id}")
def get_badge_by_id(id: int):
    return {"badges": utilities.get_user.from_id(id).badges}

@user.patch("/badges/{id}")
async def patch_user_badges(body: BadgesJsonBody, id: int, request: Request):
    conn = util.make_connection()

    if not is_perm_level(
        request.headers.get("Authorization"), ["moderator", "developer", "admin"]
    ):
        raise HTTPException(403, "You can't do this!")

    badge_str = str(body.badges).replace("'", '"')

    util.log(badge_str)

    try:
        util.exec_query(
            conn,
            """UPDATE users 
                SET badges = :badges
                WHERE rowid = :id""",
            badges=badge_str,
            id=id,
        )
    except sqlite3.Error as err:
        util.weblogs.error("Whoopsie!", traceback.print_exc())
        conn.rollback()
        raise HTTPException(500, "Database Error") from err
    conn.commit()
    return "Success!"


@user.get("/staff/{role}")
def get_staff_role(role: str):
    conn = util.make_connection()
    if role not in ["admin", "moderator", "helper"]:
        raise HTTPException(400, "Role has to be staff role")
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


@user.get("/staff/roles")
def get_all_roles():
    return json.load(Path(config.DATA + "roles.json").open("r+"))


@user.get("/{username}")
def get_by_username(username: str, request: Request):
    # TODO: mods can see banned users
    u = utilities.get_user.from_username(username)
    if not u:
        raise HTTPException(404, "User does not exist")

    return_data = {
        "username": u.username,
        "id": u.id,
        "role": u.role,
        "bio": u.bio,
        "profile_icon": u.profile_icon,
        "badges": u.badges,
        "join_date": u.join_date,
    }

    if request.headers.get("Authorization"):
        usr = auth_util.authenticate(request.headers.get("Authorization"))
        if usr == 32:
            raise HTTPException(400, "Please make sure authorization type = Basic")
        if usr == 33:
            raise HTTPException(401, "Token Expired")

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

@user.get("/id/{id}")
def get_user_by_id(id: int, request: Request):
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
        "join_date": u.join_date,
    }

    if request.headers.get("Authorization"):
        usr = auth_util.authenticate(request.headers.get("Authorization"))
        if usr == 32:
            raise HTTPException(400, "Please make sure authorization type = Basic")
        if usr == 33:
            raise HTTPException(401, "Token Expired")

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



@user.patch("/id/{id}")
def patch_user_by_id(id: int, request: Request, data: UserEditBody):
    # TODO: mods can see banned users
    usr = auth_util.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    if usr == 33:
        raise HTTPException(401, "Token Expired")

    banned = util.get_user_ban_data(usr.id)
    if banned is not None:
        raise HTTPException(403, {
            "banned": True,
            "reason": banned["reason"],
            "expires": banned["expires"],
        })

    if not (usr.id == id or usr.role in ["moderator", "admin"]):
        return "You aren't allowed to edit this user!", 403

    if len(data.username) > 32:
        return "Username too long", 400
    if len(data.bio) > 500:
        return "Bio too long", 400

    conn = util.make_connection()
    try:
        util.exec_query(
            conn,
            "UPDATE users SET username = :name, bio = :bio where rowid = :id",
            name=data.username,
            bio=data.bio,
            id=id,
        )
        if usr.role == "admin":
            util.exec_query(
                conn,
                "UPDATE users SET role = :role where rowid = :id",
                role=data.role,
                id=id,
            )
            utilities.weblogs.site_log(
                usr.username,
                "Edited user",
                f"Edited user data of {data['username']}",
            )
    except sqlite3.Error:
        conn.rollback()

        return "Something went a little bit wrong"
    conn.commit()

    return "done!"


@user.get("/me")
def get_self(request: Request):
    if not request.headers.get("Authorization"):
        raise HTTPException(401, "Authentication Required")

    usr = auth_util.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    if usr == 33:
        raise HTTPException(401, "Token Expired")

    # User Data
    user_data = {
        "username": usr.username,
        "id": usr.id,
        "role": usr.role,
        "bio": usr.bio,
        "profile_icon": usr.profile_icon,
        "join_date": usr.join_date,
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


@user.get("/me/log_out")
def log_out_self(request: Request):
    if not request.headers.get("Authorization"):
        return "You can't log yourself out if you're not logged in", 400

    usr = auth_util.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    if usr == 33:
        raise HTTPException(401, "Token Expired, or already logged out?")
    
    auth_util.log_user_out(usr.id)
    return "Successfully signed out!"


@user.get("/{username}/projects")
def get_user_projects(username: str, request: Request):
    conn = util.make_connection()

    # Check if user is authenticated
    t = request.headers.get("Authorization")
    user = utilities.get_user.from_username(username)
    authed = auth_util.authenticate(t)
    if authed == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    if authed == 33:
        raise HTTPException(401, "Token Expired")

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

                    raise HTTPException(500, "Something bad happened!") from None

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

                    raise HTTPException(500, "Something bad happened") from None

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

                raise HTTPException(500, "Something bad happened") from None

            out.append(temp)

        return {"count": len(out), "result": out}


@user.post("/id/{id}/follow")
def follow_user(id: int, request: Request):
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
