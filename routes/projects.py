"""
**Projects API endpoints**
"""

import math
import secrets
import sqlite3
import time
import traceback
from typing import Any

import bleach
import regex as re
from flask import Blueprint, Request, Response, request
from flask_cors import CORS
from sqlalchemy import Connection, Row, text
import sqlalchemy.exc

import config
import utilities.auth_utils
import utilities.weblogs
from utilities import files, get_user, util
from utilities.commons import User

projects = Blueprint("projects", __name__, url_prefix="/projects")

CORS(projects)


@projects.after_request
def after(response: Response):
    header = response.headers
    header["Access-Control-Allow-Credentials"] = "true"
    # Other headers can be added here if needed
    return response


def parse_project(
    output: Row[Any], request: Request, conn: Connection
) -> dict[str, Any]:
    this_user = utilities.auth_utils.authenticate(request.headers.get("Authorization"))

    latest_version = util.exec_query(
        conn,
        "SELECT * FROM versions WHERE project = :out0 ORDER BY rowid DESC",
        out0=output[0],
    ).all()

    user = get_user.from_id(output[2])

    if user is None:
        return {}

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


def search(conn, query, sort_by, tags, page):
    if sort_by == "updated":
        order_by = "updated DESC"
    elif sort_by == "downloads":
        order_by = "downloads DESC"
    else:
        raise ValueError("Unknown sorting method.")

    base_query = """
        SELECT rowid, * 
        FROM projects 
        WHERE status = 'live' 
        AND LOWER(TRIM(title)) LIKE :q 
    """

    parameters = {
        "q": f"%{query}%",
        "offset": (page - 1) * 24,
        "limit": page * 24,
    }

    if tags:
        parameters["c"] = f"%{tags}%"
        base_query += "AND LOWER(TRIM(category)) LIKE :c "

    full_query = base_query + f"ORDER BY {order_by} LIMIT :offset, :limit"

    return util.exec_query(conn, full_query, **parameters).all()


def count_total(conn, query, tags):
    sql_query = """
        SELECT COUNT(1)
        FROM projects
        WHERE status = 'live'
    """

    parameters = {}

    if query:
        parameters["q"] = f"%{query}%"
        sql_query += "AND LOWER(TRIM(title)) LIKE :q\n"

    if tags:
        parameters["c"] = f"%{tags}%"
        sql_query += "AND LOWER(TRIM(category)) LIKE :c"

    matching_count = util.exec_query(conn, sql_query, **parameters).first()

    return matching_count[0] if matching_count else 0


@projects.route("/search", methods=["GET"])
def search_projects() -> dict[str, Any] | tuple[str, int]:
    x = time.perf_counter()
    query = request.args.get("query", "")
    page = int(request.args.get("page", 1))
    sort = request.args.get("sort", "updated")
    tags = request.args.get("category", "")

    if len(query) > 75:
        return "Query too long!", 400

    if page < 1:
        return {
            "count": 0,
            "time": 0,
            "result": [],
            "pages": 0,
        }

    conn = util.make_connection()

    result = None

    try:
        result = search(conn, query, sort, tags, page)
    except ValueError:
        return "Unknown sorting method.", 400

    out: list[dict[str, Any]] = []

    for item in result:
        try:
            temp = parse_project(item, request, conn)
        except sqlalchemy.exc.SQLAlchemyError:
            conn.rollback()

            return "Something bad happened", 500

        out.append(temp)

    total_count = count_total(conn, query, tags)

    y = time.perf_counter()
    return {
        "count": total_count,
        "time": y - x,
        "result": out,
        "pages": math.ceil(total_count / 24),
    }


@projects.route("/id/<int:id>")
def get_project_by_id(id: int) -> dict[str, Any] | tuple[str, int]:
    conn = util.make_connection()

    this_user = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if this_user == 32:
        return "Make sure authorization is basic!", 400
    elif this_user == 33:
        return "Token expired!", 401

    proj = util.exec_query(
        conn, "select rowid, * from projects where rowid = :id", id=id
    ).one_or_none()

    if proj is None:
        return "Not found", 404

    if proj[8] in ["disabled", "draft", "unpublished", "review_queue", "publish_queue"]:
        if not this_user:
            return "Not found", 404
        if (
            this_user == 31
            or proj[3] != this_user.id
            and this_user.role not in ["admin", "moderator"]
        ):
            return "Not found", 404

    try:
        temp = parse_project(proj, request, conn)
    except:
        conn.rollback()

        return "Something bad happened", 500

    return temp


@projects.route("/get/<string:slug>")
def get_project_by_slug(slug: str) -> dict[str, Any] | tuple[str, int]:
    # connect to the thingy
    conn = util.make_connection()

    # do we need auth? no
    # do we have auth? yes
    # this is an accurate representation of minecraft 1.15
    # auth:
    this_user = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if this_user == 32:
        return "Make sure authorization is basic!", 400
    elif this_user == 33:
        return "Token expired!", 401

    # gimme dat project and gtfo
    proj = util.exec_query(
        conn, "select rowid, * from projects where url = :url", url=slug
    ).one_or_none()

    # hey u didn't give me a project, hate u
    if proj is None:
        return "Not found", 404

    if proj[8] in ["disabled", "draft", "unpublished", "review_queue", "publish_queue"]:
        if not this_user or this_user == 31:
            return "Not found", 404
        if proj[2] != this_user.id and this_user.role not in ["admin", "moderator"]:
            return "Not found", 404

    try:
        temp = parse_project(proj, request, conn)
    except:
        conn.rollback()

        return "Something bad happened", 500

    return temp


@projects.route("/random")
def random_project() -> dict[str, Any] | tuple[str, int]:
    count = request.args.get("count", 1)

    conn = util.make_connection()
    proj = util.exec_query(
        conn,
        "SELECT rowid, * FROM projects where status = 'live' ORDER BY RANDOM() LIMIT :count",
        count=count,
    ).all()

    out: list[dict[str, Any]] = []
    for i in proj:
        temp = parse_project(i, request, conn)

        out.append(temp)

    return {"count": count, "result": out}


@projects.route("/count")
def count():
    conn = util.make_connection()
    return {"count": count_total(conn, None, None)}


@projects.route("/create", methods=["POST"])
def create_new_project():
    # Check authentication
    tok = request.headers.get("Authorization")

    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 31:
        return "Provide Authorization header!", 400
    elif user == 33:
        return "Token expired!", 401

    banned = util.get_user_ban_data(user.id)
    if banned is not None:
        return {
            "banned": True,
            "reason": banned["reason"],
            "expires": banned["expires"],
        }, 403

    data = request.get_json(force=True)

    try:
        data["type"]
        data["url"]
        data["title"]
        data["description"]
        data["body"]
        data["category"]
    except KeyError:
        return "Missing field", 400

    if data["type"] not in config.valid_types:
        return f"Type {bleach.clean(data['type'])} is not a valid type! Acceptable content types: {config.valid_types}"

    if len(data["title"]) > 50:
        return "Title exceeds max length!", 400

    if len(data["description"]) > 200:
        return "Description exceeds max length", 400

    if len(data["category"]) > 3:
        return "Categories exceed 3", 400

    if (
        len(data["url"]) > 50
        and re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", data["url"]) is not None
    ):
        return "Slug is invalid!", 400

    if not re.match(r'^[\w!@$()`.+,"\-\']{3,64}$', data["url"]):
        return "URL is invalid!", 400
    
    conn = util.make_connection()
    other_project_with_slug = util.exec_query(conn, "SELECT url FROM projects WHERE url = :slug", slug=data["url"]).first()
    
    if other_project_with_slug is not None:
        return "A project with that URL already exists!", 400

    icon = None
    if data.get("icon"):
        icon = files.upload_file(
            data["icon"],
            f"icons/{secrets.randbelow(999999)!s}.avif",
            user.username,
            True,
        )

    if type(icon) is tuple or None:
        return "Error uploading icon!", 500

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
            type=data["type"],
            id=user.id,
            title=data["title"],
            desc=data["description"],
            body=data["body"],
            categories=cat_str,
            url=data["url"],
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
            type=data["type"],
            id=user.id,
            title=data["title"],
            desc=data["description"],
            body=data["body"],
            categories=cat_str,
            url=data["url"],
            uploaded=str(int(time.time())),
            updated=str(int(time.time())),
        )

    return "done", 200


@projects.route("/edit/<int:id>", methods=["POST"])
def edit_project(id: int):
    # Check authentication
    tok = request.headers.get("Authorization")

    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 31:
        return "Provide Authorization header!", 400
    elif user == 33:
        return "Token expired!", 401

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
        return "You don't have permission to edit this project. ", 403

    data = request.get_json(force=True)

    try:
        data["title"]
        data["description"]
        data["body"]
        data["category"]
    except KeyError:
        return "Missing field", 400

    if len(data["title"]) > 50:
        return "Title exceeds max length!", 400

    if len(data["description"]) > 200:
        return "Description exceeds max length", 400

    if len(data["category"]) > 3:
        return "Categories exceed 3", 400

    icon = None
    if data.get("icon"):
        icon = files.upload_file(
            data["icon"],
            f"icons/{secrets.randbelow(999999)!s}.avif",
            user.username,
            True,
        )

    if type(icon) is tuple or None:
        return "Error uploading icon!", 500

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
                title=data["title"],
                desc=data["description"],
                body=data["body"],
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
                title=data["title"],
                desc=data["description"],
                body=data["body"],
                cat=cat_str,
                id=id,
            )
    except sqlite3.Error:
        conn.rollback()

        utilities.weblogs.error("Error updating project", traceback.format_exc())
        return "Something went wrong.", 500

    conn.commit()

    if user.role in ["admin", "moderator"]:
        utilities.weblogs.site_log(
            user.username, "Edited project", f"Edited the project {data['title']}"
        )

    return "done", 200


@projects.route("/id/<int:id>/publish", methods=["POST"])
def publish(id: int):
    tok = request.headers.get("Authorization")
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 31:
        return "Provide Authorization header!", 400
    elif user == 33:
        return "Token expired!", 401

    conn = util.make_connection()
    proj = util.exec_query(
        conn,
        "select author, status, title, description, icon, url from projects where rowid = :id",
        id=id,
    ).one_or_none()

    if proj is None:
        return "Project not found.", 404

    if proj[0] != user.id:
        return "Not your project.", 403

    # now onto the fun stuff >:)
    if proj[1] == "unpublished":
        util.exec_query(
            conn,
            "update projects set status = 'publish_queue' where rowid = :id",
            id=id,
        )

        conn.commit()

        utilities.weblogs.in_queue(proj[2], proj[3], proj[4], proj[0], proj[5])
        return "The project is now in the publish queue.", 200
    elif proj[1] == "draft":  # why this?
        util.exec_query(
            conn, "update projects set status = 'live' where rowid = :id", id=id
        )

        conn.commit()

        return "The project is now live.", 200
    elif proj[1] == "disabled":
        util.exec_query(
            conn, "update projects set status = 'review_queue' where rowid = :id", id=id
        )

        conn.commit()

        utilities.weblogs.in_queue(proj[2], proj[3], proj[4], proj[0], proj[5])
        return "The project is now in the review queue.", 200
    else:
        return "This project is not in a valid state to be published!", 400


@projects.route("/id/<int:id>/draft", methods=["POST"])
def draft(id: int):
    tok = request.headers.get("Authorization")
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 31:
        return "Provide Authorization header!", 400
    elif user == 33:
        return "Token expired!", 401

    conn = util.make_connection()
    proj = util.exec_query(
        conn, "select author, status from projects where rowid = :id", id=id
    ).one_or_none()

    if not proj:
        return "Project not found.", 404

    proj = proj[0]

    if proj[0] != user.id:
        return "Not your project.", 403

    # now onto the fun stuff >:)
    if proj[1] == "live":
        util.exec_query(
            conn, "update projects set status = 'draft' where rowid = :id", id=id
        )

        conn.commit()

        return "The project is now drafted.", 200
    else:
        return "This project is not in a valid state to be drafted!", 400


@projects.route("/id/<int:id>/report", methods=["POST"])
def report(id: int):
    tok = request.headers.get("Authorization")
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 31:
        return "Provide Authorization header!", 400
    elif user == 33:
        return "Token expired!", 401

    conn = util.make_connection()
    proj = util.exec_query(
        conn, "select author from projects where rowid = :id", id=id
    ).all()

    if not proj:
        return "Project not found.", 404

    report_data = request.get_json(force=True)

    # now onto the fun stuff >:)
    try:
        report_data["message"]
    except KeyError:
        return "Please provide a `message` field."
    else:
        util.exec_query(
            conn,
            "insert into reports values (:msg, :uid, :pid)",
            msg=report_data["message"],
            uid=user.id,
            pid=id,
        )
        conn.commit()

        return "didded", 200


@projects.route("/id/<int:id>/remove", methods=["POST"])
def remove(id: int):
    tok = request.headers.get("Authorization")
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 31:
        return "Provide Authorization header!", 400
    elif user == 33:
        return "Token expired!", 401

    conn = util.make_connection()
    proj = util.exec_query(
        conn, "select author, status from projects where rowid = :id", id=id
    ).all()

    if not proj:
        return "Project not found.", 404

    proj = proj[0]

    if proj[0] != user.id and user.role not in ["admin", "moderator"]:
        return "Not your project.", 403

    # now onto the fun stuff >:)
    if proj[1] != "deleted":
        util.exec_query(
            conn, "update projects set status = 'deleted' where rowid = :id", id=id
        )

        conn.commit()

        return "The project is now deleted.", 200
    else:
        return "This project is not in a valid state to be deleted!", 400


@projects.route("/id/<int:id>/download", methods=["POST"])
def download(id: int):
    tok = request.headers.get("Authorization")
    if tok != config.FILE_SERVER_TOKEN:
        return "This is a private route!", 403

    conn = util.make_connection()
    proj = util.exec_query(
        conn, "select downloads from projects where rowid = :id", id=id
    ).one_or_none()

    if not proj:
        return "Project not found.", 404

    util.exec_query(
        conn, "update projects set downloads = downloads + 1 where rowid = :id", id=id
    )

    conn.commit()

    return "Incremented download counter.", 200


@projects.route("/id/<int:id>/feature", methods=["POST"])
def feature(id: int):
    # Authenticate
    tok = request.headers.get("Authorization")
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401
    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 33:
        return "Token expired!", 401
    elif user == 31:
        return "Provide Authorization header!", 400
    if user.role not in ["admin", "moderator"]:
        return "You don't have permission to do this", 403

    dat = request.get_json(force=True)
    try:
        dat["expires"]
    except KeyError:
        return "Expiry parameter missing", 400

    # Validate project
    conn = util.make_connection()
    proj = util.exec_query(
        conn, "select author, status, title, url from projects where rowid = :id", id=id
    ).all()

    if not proj:
        return "Project not found.", 404

    proj = proj[0]

    # now onto the fun stuff >:)
    if proj[1] != "live":
        return "This project is not in a valid state to be featured!", 400

    current = time.time()
    expiry = current + (86400 * dat["expires"])

    try:
        util.exec_query(
            conn,
            "UPDATE projects SET featured_until = :expiry WHERE rowid = :id",
            expiry=expiry,
            id=id,
        )
    except sqlite3.Error:
        conn.rollback()

        return "There was an error."
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
def featured() -> dict[str, Any] | tuple[str, int]:
    conn = util.make_connection()
    proj = conn.execute(
        text(
            "SELECT rowid, * FROM projects where status = 'live' and featured_until > 0"
        )
    ).all()

    out: list[dict[str, Any]] = []
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
                temp = parse_project(i, request, conn)
            except:
                conn.rollback()

                return "Something bad happened", 500

            out.append(temp)

    return {"result": out, "count": proj.__len__()}
