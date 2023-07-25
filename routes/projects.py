"""
**Projects API endpoints**
"""

import math
import secrets
import sqlite3
import time
import traceback

import regex as re
from flask import Blueprint, request
from flask_cors import CORS

import config
import utilities.auth_utils
import utilities.files as files
import utilities.post
import utilities.util as util
import utilities.get_user as get_user

projects = Blueprint("projects", __name__, url_prefix="/projects")

CORS(projects)


@projects.after_request
def after(resp):
    header = resp.headers
    header["Access-Control-Allow-Credentials"] = "true"
    # Other headers can be added here if needed
    return resp


def parse_project(output: tuple, conn: sqlite3.Connection):
    latest_version = conn.execute(
        f"SELECT * FROM versions WHERE project = {output[0]} ORDER BY rowid DESC"
    ).fetchall()

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

    if output[14]:
        temp["featured"] is True

    if len(latest_version) != 0:
        temp["latest_version"] = {
            "name": latest_version[0][0],
            "description": latest_version[0][1],
            "minecraft_versions": latest_version[0][4],
            "version_code": latest_version[0][5],
        }

    return temp


@projects.route("/search", methods=["GET"])
def search():
    x = time.time()
    query = request.args.get("query", "").replace("'", "")
    page = int(request.args.get("page", 1))
    sort = request.args.get("sort", "updated")

    if len(query) > 75:
        return

    page = request.args.get("page", 1)

    conn = sqlite3.connect(config.DATA + "data.db")
    if sort == "updated":
        r = conn.execute(
            f"select rowid, * from projects where status = 'live' and trim(title) LIKE '%{util.clean(query)}%' ORDER BY updated DESC"
        ).fetchall()
    elif sort == "downloads":
        r = conn.execute(
            f"select rowid, * from projects where status = 'live' and trim(title) LIKE '%{util.clean(query)}%' ORDER BY downloads DESC"
        ).fetchall()
    else:
        return "Unknown sorting method.", 400

    out = []

    for item in r[(page - 1) * 20 : page * 20 - 1]:
        try:
            temp = parse_project(item, conn)
        except:
            conn.rollback()
            conn.close()
            return "Something bad happened", 500

        out.append(temp)

    conn.close()

    y = time.time()
    return {
        "count": len(out),
        "time": y - x,
        "result": out,
        "pages": str(math.ceil(len(r) / 20)),
    }


@projects.route("/", methods=["GET"])
def query():
    page = request.args.get("page", 1)
    page = int(page)
    sort = request.args.get("sort", "updated")

    # SQL stuff
    conn = sqlite3.connect(config.DATA + "data.db")
    if sort == "updated":
        r = conn.execute(
            "select rowid, * from projects where status = 'live' ORDER BY updated DESC"
        ).fetchall()
    elif sort == "downloads":
        r = conn.execute(
            "select rowid, * from projects where status = 'live' ORDER BY downloads DESC"
        ).fetchall()
    else:
        return "Unknown sorting method.", 400

    out = []

    for item in r[(page - 1) * 20 : page * 20 - 1]:
        try:
            temp = parse_project(item, conn)
        except:
            conn.rollback()
            conn.close()
            return "Something bad happened", 500

        out.append(temp)

    conn.close()

    return {"count": len(out), "result": out, "pages": str(math.ceil(len(r) / 20))}


@projects.route("/id/<int:id>")
def get_proj(id):
    conn = sqlite3.connect(config.DATA + "data.db")

    this_user = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if this_user == 32:
        return "Make sure authorization is basic!", 400
    elif this_user == 33:
        return "Token expired!", 401

    proj = conn.execute(f"select rowid, * from projects where rowid = {id}").fetchone()

    if not proj:
        return "Not found", 404

    if (
        proj[8] == "disabled"
        or proj[8] == "draft"
        or proj[8] == "unpublished"
        or proj[8] == "review_queue"
        or proj[8] == "publish_queue"
    ):
        if not this_user:
            return "Not found", 404
        if proj[1] != this_user.id and this_user.role not in ["admin", "moderator"]:
            return "Not found", 404

    try:
        temp = parse_project(proj, conn)
    except:
        conn.rollback()
        conn.close()
        return "Something bad happened", 500

    conn.close()

    return temp


@projects.route("/get/<string:slug>")
def get_project(slug: str):
    # connect to the thingy
    conn = sqlite3.connect(config.DATA + "data.db")

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
    proj = conn.execute(
        f"select rowid, * from projects where url = '{util.clean(slug)}'"
    ).fetchone()

    # hey u didn't give me a project, hate u
    if not proj:
        return "Not found", 404

    if proj[8] in ["disabled", "draft", "unpublished", "review_queue", "publish_queue"]:
        if not this_user:
            return "Not found", 404
        if proj[1] != this_user.id and this_user.role not in ["admin", "moderator"]:
            return "Not found", 404

    try:
        temp = parse_project(proj, conn)
    except:
        conn.rollback()
        conn.close()
        return "Something bad happened", 500

    conn.close()
    return temp


@projects.route("/random")
def random():
    count = request.args.get("count", 1)

    conn = sqlite3.connect(config.DATA + "data.db")
    proj = conn.execute(
        f"SELECT rowid, * FROM projects where status = 'live' ORDER BY RANDOM() LIMIT {util.clean(count)}"
    ).fetchall()

    out = []
    for i in proj:
        try:
            temp = parse_project(proj, conn)
        except:
            conn.rollback()
            conn.close()
            return "Something bad happened", 500

        out.append(temp)

    conn.close()
    return {"count": count, "result": out}


@projects.route("/count")
def count():
    conn = sqlite3.connect(config.DATA + "data.db")
    x = (
        conn.execute("select * from projects where status = 'live'")
        .fetchall()
        .__len__()
    )
    conn.close()
    return {"count": x}


@projects.route("/create", methods=["POST"])
def new_project():
    # Check authentication
    tok = request.headers.get("Authorization")

    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
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
        return f"Type {data['type']} is not a valid type! Acceptable content types: {config.valid_types}"

    if len(data["title"]) > 50:
        return "Title exceeds max length!", 400

    if len(data["description"]) > 200:
        return "Description exceeds max length", 400

    if len(data["category"]) > 3:
        return "Categories exceed 3", 400

    if not re.match(r'^[\w!@$()`.+,"\-\']{3,64}$', data["url"]):
        return "URL is bad", 400

    if "icon" in data and data["icon"]:
        icon = files.upload_file(
            data["icon"],
            f"icons/{str(secrets.randbelow(999999))}.png",
            user.username,
        )

    # Update database
    conn = sqlite3.connect(config.DATA + "data.db")

    cat_str = ",".join(data["category"])

    if "icon" in data and data["icon"]:
        conn.execute(
            f"""insert into projects(
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
                        '{util.clean(data['type'])}', 
                        {user.id}, 
                        '{util.clean(data['title'])}', 
                        '{util.clean(data['description'])}', 
                        '{util.clean(data['body'])}',
                        '{util.clean(cat_str)}', 
                        '{util.clean(data['url'])}', 
                        'unpublished',
                        {str(int(time.time()))},
                        {str(int(time.time()))},
                        '{icon}')"""
        )
    else:
        conn.execute(
            f"""insert into projects(
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
                        '{util.clean(data['type'])}', 
                        {user.id}, 
                        '{util.clean(data['title'])}', 
                        '{util.clean(data['description'])}', 
                        '{util.clean(data['body'])}',
                        '{util.clean(cat_str)}', 
                        '{util.clean(data['url'])}', 
                        'draft',
                        {str(int(time.time()))},
                        {str(int(time.time()))})"""
        )

    conn.commit()
    conn.close()

    return "done", 200


@projects.route("/edit/<int:id>", methods=["POST"])
def edit(id: int):
    # Check authentication
    tok = request.headers.get("Authorization")

    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
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
        or user.id in ["admin", "moderator"]
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

    if "icon" in data and data["icon"]:
        icon = files.upload_file(
            data["icon"],
            f"icons/{str(secrets.randbelow(999999))}.png",
            user.username,
        )

    # Update database
    conn = sqlite3.connect(config.DATA + "data.db")

    cat_str = ",".join(data["category"])

    try:
        if "icon" in data and data["icon"]:
            conn.execute(
                f"""update projects set
                title = '{util.clean(data["title"])}',
                description = '{util.clean(data["description"])}',
                body = '{util.clean(data["body"])}',
                category = '{util.clean(cat_str)}',
                icon = '{icon}' 
                where rowid = {id}"""
            )
        else:
            conn.execute(
                f"""update projects set
                title = '{util.clean(data["title"])}',
                description = '{util.clean(data["description"])}',
                body = '{util.clean(data["body"])}',
                category = '{util.clean(cat_str)}' 
                where rowid = {id}"""
            )
    except sqlite3.Error:
        conn.rollback()
        utilities.post.error("Error updating project", traceback.format_exc())
        return "Something went wrong.", 500

    conn.commit()
    conn.close()

    if user.role in ["admin", "moderator"]:
        utilities.post.site_log(
            user.username, "Edited project", f"Edited the project {data['title']}"
        )

    return "done", 200


@projects.route("/id/<int:id>/publish", methods=["POST"])
def publish(id):
    tok = request.headers.get("Authorization")
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 33:
        return "Token expired!", 401

    conn = sqlite3.connect(config.DATA + "data.db")
    proj = conn.execute(
        "select author, status, title, description, icon, url from projects where rowid = "
        + str(id)
    ).fetchall()

    if len(proj) == 0:
        return "Project not found.", 404

    proj = proj[0]

    if proj[0] != user.id:
        return "Not your project.", 403

    # now onto the fun stuff >:)
    if proj[1] == "unpublished":
        conn.execute(
            "update projects set status = 'publish_queue' where rowid = " + str(id)
        )

        conn.commit()
        conn.close()
        utilities.post.in_queue(proj[2], proj[3], proj[4], proj[0], proj[5])
        return "The project is now in the publish queue.", 200
    elif proj[1] == "draft":
        conn.execute("update projects set status = 'live' where rowid = " + str(id))

        conn.commit()
        conn.close()
        return "The project is now live.", 200
    elif proj[1] == "disabled":
        conn.execute(
            "update projects set status = 'review_queue' where rowid = " + str(id)
        )

        conn.commit()
        conn.close()
        utilities.post.in_queue(proj[2], proj[3], proj[4], proj[0], proj[5])
        return "The project is now in the review queue.", 200
    else:
        return "This project is not in a valid state to be published!", 400


@projects.route("/id/<int:id>/draft", methods=["POST"])
def draft(id):
    tok = request.headers.get("Authorization")
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 33:
        return "Token expired!", 401

    conn = sqlite3.connect(config.DATA + "data.db")
    proj = conn.execute(
        "select author, status from projects where rowid = " + str(id)
    ).fetchall()

    if len(proj) == 0:
        return "Project not found.", 404

    proj = proj[0]

    if proj[0] != user.id:
        return "Not your project.", 403

    # now onto the fun stuff >:)
    if proj[1] == "live":
        conn.execute("update projects set status = 'draft' where rowid = " + str(id))

        conn.commit()
        conn.close()
        return "The project is now drafted.", 200
    else:
        return "This project is not in a valid state to be drafted!", 400


@projects.route("/id/<int:id>/report", methods=["POST"])
def report(id):
    tok = request.headers.get("Authorization")
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 33:
        return "Token expired!", 401

    conn = sqlite3.connect(config.DATA + "data.db")
    proj = conn.execute(
        "select author from projects where rowid = " + str(id)
    ).fetchall()

    if len(proj) == 0:
        return "Project not found.", 404

    report_data = request.get_json(force=True)

    # now onto the fun stuff >:)
    try:
        report_data["message"]
    except KeyError:
        return "Please provide a `message` field."
    else:
        conn.execute(
            f"insert into reports values ('{util.clean(report_data['message'])}', {user.id}, {id})"
        )
        conn.commit()
        conn.close()
        return "didded", 200


@projects.route("/id/<int:id>/remove", methods=["POST"])
def remove(id):
    tok = request.headers.get("Authorization")
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 33:
        return "Token expired!", 401

    conn = sqlite3.connect(config.DATA + "data.db")
    proj = conn.execute(
        "select author, status from projects where rowid = " + str(id)
    ).fetchall()

    if len(proj) == 0:
        return "Project not found.", 404

    proj = proj[0]

    if proj[0] != user.id and user.role not in ["admin", "moderator"]:
        return "Not your project.", 403

    # now onto the fun stuff >:)
    if proj[1] != "deleted":
        conn.execute("update projects set status = 'deleted' where rowid = " + str(id))

        conn.commit()
        conn.close()
        return "The project is now deleted.", 200
    else:
        return "This project is not in a valid state to be deleted!", 400


@projects.route("/id/<int:id>/download", methods=["POST"])
def download(id):
    tok = request.headers.get("Authorization")
    if tok != "ThisIsVeryLegitComeFromCDNNotSpoofedBroTrustMe12":
        return "This is a private route!", 403

    conn = sqlite3.connect(config.DATA + "data.db")
    proj = conn.execute(
        "select downloads from projects where rowid = " + str(id)
    ).fetchall()

    if len(proj) == 0:
        return "Project not found.", 404

    conn.execute(
        "update projects set downloads = downloads + 1 where rowid = " + str(id)
    )

    conn.commit()
    conn.close()
    return "Incremented download counter.", 200


@projects.route("/id/<int:id>/feature", methods=["POST"])
def feature(id):
    # Authenticate
    tok = request.headers.get("Authorization")
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401
    user = utilities.auth_utils.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 33:
        return "Token expired!", 401
    if user.role not in ["admin", "moderator"]:
        return "You don't have permission to do this", 403

    dat = request.get_json(force=True)
    try:
        dat["expires"]
    except KeyError:
        return "Expiry parameter missing", 400

    # Validate project
    conn = sqlite3.connect(config.DATA + "data.db")
    proj = conn.execute(
        "select author, status, title, url from projects where rowid = " + str(id)
    ).fetchall()

    if len(proj) == 0:
        return "Project not found.", 404

    proj = proj[0]

    # now onto the fun stuff >:)
    if proj[1] != "live":
        return "This project is not in a valid state to be featured!", 400

    current = time.time()
    expiry = current + (86400 * dat["expires"])

    try:
        conn.execute(
            f"UPDATE projects SET featured_until = {str(expiry)} WHERE rowid = {str(id)}"
        )
    except sqlite3.Error:
        conn.rollback()
        conn.close()
        return "There was an error."
    else:
        conn.execute(
            f"INSERT INTO notifs VALUES ('Project Featured', 'Your project, [{proj[2]}](https://datapackhub.net/project/{proj[3]}), was featured by a moderator for {dat['expires']} days. During this time, it will be visible on the front page and higher up in search results. Congrats! :D', False,  'announcement', {proj[0]})"
        )
        conn.commit()
        conn.close()
        # util.post.fea(user.username, project[2], project[4], project[5], project[3], data["message"])
        return "Featured project!"


@projects.route("/featured")
def featured():
    conn = sqlite3.connect(config.DATA + "data.db")
    proj = conn.execute(
        "SELECT rowid, * FROM projects where status = 'live' and featured_until > 0"
    ).fetchall()

    out = []
    for i in proj:
        if time.time() > i[14]:
            conn.execute(
                f"update projects set featured_until = null where rowid = {i[6]}"
            )
            conn.commit()
        else:
            try:
                temp = parse_project(i, conn)
            except:
                conn.rollback()
                conn.close()
                return "Something bad happened", 500

            out.append(temp)

    conn.close()
    return {"result": out, "count": proj.__len__()}
