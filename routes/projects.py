"""
**Projects API endpoints**
"""

import math
import secrets
import sqlite3
import time
import traceback

import bleach
from fastapi import APIRouter, HTTPException, Request
import regex as re
from sqlalchemy import Engine, text

import config
import utilities.auth_utils
from utilities.request_types import EditProjectBody, PostNewProjectBody
import utilities.weblogs
from utilities import files, get_user, util
from utilities.commons import FeaturedData, ReportData, User

projects = APIRouter(prefix="/projects", tags=["projects"])


def parse_project(output: tuple, conn: Engine, request: Request):
    this_user = utilities.auth_utils.authenticate(request.headers.get("Authorization"))

    latest_version = util.exec_query(
        conn,
        "SELECT * FROM versions WHERE project = :out0 ORDER BY rowid DESC",
        out0=output[0],
    ).all()

    user = get_user.from_id(output[2])

    temp = {
        "ID": output[0],
        "type": output[1],
        "author": {
            "username": user.username,
            "id": user.id,
            "role": user.role,
            "bio": user.bio,
            "profile_icon": user.profile_icon,
            "badges": user.badges,
        },
        "title": output[3],
        "description": output[4],
        "body": output[5],
        "icon": output[6],
        "url": output[7],
        "status": output[8],
        "category": str(output[9]).split(","),
        "uploaded": output[10],
        "updated": output[11],
        "downloads": output[13],
        "featured": False,
        "licence": output[15],
        "dependencies": str(output[9]).split(","),
    }

    if (
        type(this_user) is User
        and (this_user.id == output[2] or this_user.role in ["moderator", "admin"])
        and output[12]
    ):
        temp["mod_message"] = output[12]

    if output[14]:
        temp["featured"] = True

    if len(latest_version) != 0:
        temp["latest_version"] = {
            "name": latest_version[0][0],
            "description": latest_version[0][1],
            "minecraft_versions": latest_version[0][4],
            "version_code": latest_version[0][5],
        }

    return temp


@projects.get("/search")
def search_projects(request: Request, query: str, page: int = 1, sort: str = "updated"):
    x = time.perf_counter()

    if len(query) > 75:
        return

    if page < 1:
        return {
            "count": 0,
            "time": 0,
            "result": [],
            "pages": 0,
        }

    conn = util.make_connection()
    if sort == "updated":
        rows = util.exec_query(
            conn,
            "select rowid, * from projects where status = 'live' and trim(title) LIKE :q ORDER BY updated DESC LIMIT :offset, :limit",
            q=f"%{query}%",
            offset=page - 1 * 20,
            limit=page * 20,
        ).all()
    elif sort == "downloads":
        rows = util.exec_query(
            conn,
            "select rowid, * from projects where status = 'live' and trim(title) LIKE :q ORDER BY downloads DESC LIMIT :offset, :limit",
            q=f"%{query}%",
            offset=page - 1 * 20,
            limit=page * 20,
        ).all()
    else:
        raise HTTPException(400, "Invalid sort type")

    out = []

    for item in rows:
        try:
            temp = parse_project(item, conn)
        except:
            conn.rollback()

            raise HTTPException(500, "Something bad happened") from None

        out.append(temp)

    y = time.perf_counter()
    return {
        "count": len(out),
        "time": y - x,
        "result": out,
        "pages": str(math.ceil(len(rows) / 20)),
    }


@projects.get("/")
def all_projects(page: int = 1, sort: str = "updated"):

    # SQL stuff
    conn = util.make_connection()
    if sort == "updated":
        r = conn.execute(
            text(
                "select rowid, * from projects where status = 'live' ORDER BY updated DESC"
            )
        ).all()
    elif sort == "downloads":
        r = conn.execute(
            text(
                "select rowid, * from projects where status = 'live' ORDER BY downloads DESC"
            )
        ).all()
    else:
        raise HTTPException(400, "Invalid sort type")

    out = []

    for item in r[(page - 1) * 20 : page * 20 - 1]:
        try:
            temp = parse_project(item, conn)
        except:
            conn.rollback()

            raise HTTPException(500, "Something Bad Happened") from None

        out.append(temp)

    return {"count": len(out), "result": out, "pages": str(math.ceil(len(r) / 20))}


@projects.get("/id/{id}")
def get_project_by_id(id: int, request: Request):
    conn = util.make_connection()

    this_user = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if this_user == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    if this_user == 33:
        raise HTTPException(401, "Token Expired")

    proj = util.exec_query(
        conn, "select rowid, * from projects where rowid = :id", id=id
    ).one_or_none()

    if proj is None:
        raise HTTPException(404, "Not found")

    if proj[8] in ["disabled", "draft", "unpublished", "review_queue", "publish_queue"]:
        if not this_user:
            raise HTTPException(404, "Not found")
        if (
            this_user == 31
            or proj[3] != this_user.id
            and this_user.role not in ["admin", "moderator"]
        ):
            raise HTTPException(404, "Not found")

    try:
        temp = parse_project(proj, conn)
    except:
        conn.rollback()

        raise HTTPException(500, "Something Bad Happened!") from None

    return temp


@projects.get("/get/{slug}")
def get_project_by_slug(slug: str, request: Request):
    # connect to the thingy
    conn = util.make_connection()

    # do we need auth? no
    # do we have auth? yes
    # this is an accurate representation of minecraft 1.15
    # auth:
    this_user = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if this_user == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    if this_user == 33:
        raise HTTPException(401, "Token Expired")

    # gimme dat project and gtfo
    proj = util.exec_query(
        conn, "select rowid, * from projects where url = :url", url=slug
    ).one_or_none()

    # hey u didn't give me a project, hate u
    if proj is None:
        raise HTTPException(404, "Not found")

    if proj[8] in ["disabled", "draft", "unpublished", "review_queue", "publish_queue"]:
        if not this_user or this_user == 31:
            raise HTTPException(404, "Not found")
        if proj[2] != this_user.id and this_user.role not in ["admin", "moderator"]:
            raise HTTPException(404, "Not found")

    try:
        temp = parse_project(proj, conn)
    except:
        conn.rollback()

        raise HTTPException(500, "Something bad happened") from None

    return temp


@projects.get("/random")
def random_project(count: int = 1):

    conn = util.make_connection()
    proj = util.exec_query(
        conn,
        "SELECT rowid, * FROM projects where status = 'live' ORDER BY RANDOM() LIMIT :count",
        count=count,
    ).all()

    out = []
    for i in proj:
        temp = parse_project(i, conn)

        out.append(temp)

    return {"count": count, "result": out}


@projects.route("/count")
def count():
    conn = util.make_connection()
    x = (
        conn.execute(text("select * from projects where status = 'live'"))
        .all()
        .__len__()
    )

    return {"count": x}


@projects.post("/create")
def create_new_project(request: Request, data: PostNewProjectBody):
    # Check authentication
    tok = request.headers.get("Authorization")

    if not tok:
        raise HTTPException(401, "Not Authed")

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    if user == 33:
        raise HTTPException(401, "Token Expired")

    banned = util.get_user_ban_data(user.id)
    if banned is not None:
        return {
            "banned": True,
            "reason": banned["reason"],
            "expires": banned["expires"],
        }, 403

    if data.type not in config.valid_types:
        return f"Type {bleach.clean(data['type'])} is not a valid type! Acceptable content types: {config.valid_types}"

    if len(data.title) > 50:
        raise HTTPException(400, "Title too long")

    if len(data.description) > 200:
        raise HTTPException(400, "Description too long")

    if len(data.category) > 3:
        raise HTTPException(400, "Categories too long")

    if len(data.url) > 50 and not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$"):
        raise HTTPException(400, "Slug invalid")

    if not re.match(r'^[\w!@$()`.+,"\-\']{3,64}$', data.url):
        raise HTTPException(400, "URL invalid")

    if data.get("icon"):
        icon = files.upload_file(
            data.icon,
            f"icons/{secrets.randbelow(999999)!s}.avif",
            user.username,
            True,
        )

    # Update database
    cat_str = ",".join(data["category"])

    if data.get("icon"):
        util.commit_query(
            """insert into projects(
                    type, 
                    author, 
                    title, 
                    description, 
                    body,
                    category, 
                    url, 
                    status,
                    uploaded,
                    updated,
                    icon) values (
                        :type, 
                        :id, 
                        :title, 
                        :desc, 
                        :body,
                        :categories, 
                        :url, 
                        'unpublished',
                        :uploaded,
                        :updated,
                        :icon)""",
            type=data.type,
            id=user.id,
            title=data.title,
            desc=data.description,
            body=data.body,
            categories=cat_str,
            url=data.url,
            uploaded=str(int(time.time())),
            updated=str(int(time.time())),
            icon=icon,
        )
    else:
        util.commit_query(
            """insert into projects(
                    type, 
                    author, 
                    title, 
                    description, 
                    body,
                    category, 
                    url, 
                    status,
                    uploaded,
                    updated) values (
                        :type, 
                        :id, 
                        :title, 
                        :desc, 
                        :body,
                        :categories, 
                        :url, 
                        'unpublished',
                        :uploaded,
                        :updated)""",
            type=data.type,
            id=user.id,
            title=data.title,
            desc=data.description,
            body=data.body,
            categories=cat_str,
            url=data.url,
            uploaded=str(int(time.time())),
            updated=str(int(time.time())),
        )

    return "done", 200


@projects.post("/edit/{id}")
def edit_project(id: int, request: Request, data: EditProjectBody):
    # Check authentication
    tok = request.headers.get("Authorization")

    if not tok:
        raise HTTPException(401, "Not authed")

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    if user == 33:
        raise HTTPException(401, "Token Expired")

    banned = util.get_user_ban_data(user.id)
    if banned is not None:
        return {
            "banned": True,
            "reason": banned["reason"],
            "expires": banned["expires"],
        }, 403

    if not (
        util.user_owns_project(project=id, author=user.id)
        or user.role in ["admin", "moderator"]
    ):
        raise HTTPException(403, "You don't have permission to edit this project. ")

    if len(data.title) > 50:
        raise HTTPException(400, "Title too long")

    if len(data.description) > 200:
        raise HTTPException(400, "Description too long")

    if len(data.category) > 3:
        raise HTTPException(400, "Categories too long")

    if data.get("icon"):
        icon = files.upload_file(
            data.icon,
            f"icons/{secrets.randbelow(999999)!s}.avif",
            user.username,
            is_icon=True,
        )

    # Update database
    conn = util.make_connection()

    cat_str = ",".join(data["category"])

    try:
        if data.get("icon"):
            util.exec_query(
                conn,
                """update projects set
                title = :title,
                description = :desc,
                body = :body,
                category = :cat,
                icon = :icon 
                where rowid = :id""",
                title=data.title,
                desc=data.description,
                body=data.body,
                cat=cat_str,
                icon=icon,
                id=id,
            )
        else:
            util.exec_query(
                conn,
                """update projects set
                title = :title,
                description = :desc,
                body = :body,
                category = :cat
                where rowid = :id""",
                title=data.title,
                desc=data.description,
                body=data.body,
                cat=cat_str,
                id=id,
            )
    except sqlite3.Error as err:
        conn.rollback()

        utilities.weblogs.error("Error updating project", traceback.format_exc())
        raise HTTPException(500, "Something went wrong.") from err

    conn.commit()

    if user.role in ["admin", "moderator"]:
        utilities.weblogs.site_log(
            user.username, "Edited project", f"Edited the project {data['title']}"
        )

    return "done"


@projects.post("/id/{id}/publish")
def publish(id: int, request: Request):
    tok = request.headers.get("Authorization")
    if not tok:
        raise HTTPException(401, "Not Authed")

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    elif user == 33:
        raise HTTPException(401, "Token Expired")

    conn = util.make_connection()
    proj = util.exec_query(
        conn,
        "select author, status, title, description, icon, url from projects where rowid = :id",
        id=id,
    ).one_or_none()

    if proj is None:
        raise HTTPException(404, "Project not found")

    if proj[0] != user.id:
        raise HTTPException(403, "Not your project")

    # now onto the fun stuff >:)
    if proj[1] == "unpublished":
        util.exec_query(
            conn,
            "update projects set status = 'publish_queue' where rowid = :id",
            id=id,
        )

        conn.commit()

        utilities.weblogs.in_queue(proj[2], proj[3], proj[4], proj[0], proj[5])
        return "The project is now in the publish queue."
    elif proj[1] == "draft":  # why this?
        util.exec_query(
            conn, "update projects set status = 'live' where rowid = :id", id=id
        )

        conn.commit()

        return "The project is now live."
    elif proj[1] == "disabled":
        util.exec_query(
            conn, "update projects set status = 'review_queue' where rowid = :id", id=id
        )

        conn.commit()

        utilities.weblogs.in_queue(proj[2], proj[3], proj[4], proj[0], proj[5])
        return "The project is now in the review queue."
    else:
        raise HTTPException(400, "Not in a valid state to be published")


@projects.post("/id/{id}/draft")
def draft(id: int, request: Request):
    tok = request.headers.get("Authorization")
    if not tok:
        raise HTTPException(401, "Not Authed")

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    elif user == 33:
        raise HTTPException(401, "Token Expired")

    conn = util.make_connection()
    proj = util.exec_query(
        conn,
        "select author, status from projects where rowid = :id",
        id=id,
    ).one_or_none()

    if proj is None:
        raise HTTPException(404, "Project not found")

    if proj[0] != user.id:
        raise HTTPException(403, "Not your project")

    # now onto the fun stuff >:)
    if proj[1] == "live":
        util.exec_query(
            conn, "update projects set status = 'draft' where rowid = :id", id=id
        )

        conn.commit()

        return "The project is now drafted."
    else:
        raise HTTPException(400, "Not in a valid draft state")


@projects.post("/id/{id}/report")
def report(id: int, request: Request, report_data: ReportData):
    tok = request.headers.get("Authorization")
    if not tok:
        raise HTTPException(401, "Not Authed")

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    elif user == 33:
        raise HTTPException(401, "Token Expired")

    conn = util.make_connection()
    proj = util.exec_query(
        conn, "select author from projects where rowid = :id", id=id
    ).all()

    if not proj:
        raise HTTPException(404, "Project not found")

    # now onto the fun stuff >:)
    util.exec_query(
        conn,
        "insert into reports values (:msg, :uid, :pid)",
        msg=report_data["message"],
        uid=user.id,
        pid=id,
    )
    conn.commit()

    return "didded"


@projects.post("/id/{id}/remove")
def remove(id: int, request: Request):
    tok = request.headers.get("Authorization")
    if not tok:
        raise HTTPException(401, "Not Authed")

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    elif user == 33:
        raise HTTPException(401, "Token Expired")

    conn = util.make_connection()
    proj = util.exec_query(
        conn, "select author, status from projects where rowid = :id", id=id
    ).all()

    if not proj:
        raise HTTPException(404, "Project not found")

    proj = proj[0]

    if proj[0] != user.id and user.role not in ["admin", "moderator"]:
        raise HTTPException(403, "Not your project")

    # now onto the fun stuff >:)
    if proj[1] != "deleted":
        util.exec_query(
            conn, "update projects set status = 'deleted' where rowid = :id", id=id
        )

        conn.commit()

        return "The project is now deleted."
    else:
        raise HTTPException(400, "Project is not in a valid state to be deleted")


@projects.post("/id/{id}/download")
def download(id: int, request: Request):
    tok = request.headers.get("Authorization")
    if tok != "ThisIsVeryLegitComeFromCDNNotSpoofedBroTrustMe12":
        raise HTTPException(403, "This route is private")

    conn = util.make_connection()
    proj = util.exec_query(
        conn, "select downloads from projects where rowid = :id", id=id
    ).one_or_none()

    if not proj:
        raise HTTPException(404, "Project not found")

    util.exec_query(
        conn, "update projects set downloads = downloads + 1 where rowid = :id", id=id
    )

    conn.commit()

    return "Incremented download counter."


@projects.post("/id/{id}/feature")
def feature(id: int, request: Request, dat: FeaturedData):
    # Authenticate
    tok = request.headers.get("Authorization")
    if not tok:
        raise HTTPException(401, "Not Authed")

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        raise HTTPException(400, "Please make sure authorization type = Basic")
    elif user == 33:
        raise HTTPException(401, "Token Expired")
    
    if user.role not in ["admin", "moderator"]:
        raise HTTPException(403, "No permission!")

    # Validate project
    conn = util.make_connection()
    proj = util.exec_query(
        conn, "select author, status, title, url from projects where rowid = :id", id=id
    ).all()

    if not proj:
        raise HTTPException(404, "Project not found!")

    proj = proj[0]

    # now onto the fun stuff >:)
    if proj[1] != "live":
        raise HTTPException(400, "Not in a valid state ot be featured")

    current = time.time()
    expiry = current + (86400 * dat["expires"])

    try:
        util.exec_query(
            conn,
            "UPDATE projects SET featured_until = :expiry WHERE rowid = :id",
            expiry=expiry,
            id=id,
        )
    except sqlite3.Error as err:
        conn.rollback()

        raise HTTPException(500, "There was an error") from err
    else:
        util.exec_query(
            conn,
            "INSERT INTO notifs VALUES (:title, :msg, False,  'announcement', :id)",
            title="Project Featured",
            msg=f"Your project, [{proj[2]}](https://datapackhub.net/project/{proj[3]}), was featured by a moderator for {dat['expires']} days. During this time, it will be visible on the front page and higher up in search results. Congrats! :D",
            id=proj[0],
        )
        conn.commit()

        return "Featured project!"


@projects.route("/featured")
def featured():
    conn = util.make_connection()
    proj = conn.execute(
        text(
            "SELECT rowid, * FROM projects where status = 'live' and featured_until > 0"
        )
    ).all()

    out = []
    for i in proj:
        if time.time() > i[14]:
            util.exec_query(
                conn,
                "update projects set featured_until = null where rowid = :id",
                id=i[0],
            )
            conn.commit()
        else:
            try:
                temp = parse_project(i, conn)
            except:
                conn.rollback()

                raise HTTPException(500, "Something bad happened") from None

            out.append(temp)

    return {"result": out, "count": len(proj)}
