"""
**Projects API endpoints**
"""

from flask_cors import CORS
from flask import Blueprint, request
import util
import json
import sqlite3
import config
import regex as re
import time
import files
import secrets
import traceback

projects = Blueprint("projects", __name__, url_prefix="/projects")

CORS(projects)


@projects.after_request
def after(resp):
    header = resp.headers
    header["Access-Control-Allow-Credentials"] = "true"
    # Other headers can be added here if needed
    return resp


@projects.route("/search", methods=["GET"])
def search():
    x = time.time()
    query = request.args.get("query").replace("'", "")

    if len(query) > 75:
        return

    page = request.args.get("page", 1)
    print(query)

    conn = sqlite3.connect(config.DATA + "data.db")
    r = conn.execute(
        f"select type, author, title, icon, url, description, rowid, category, uploaded, updated from projects where trim(title) LIKE '%{util.sanitise(query)}%'"
    ).fetchall()

    out = []

    print(r)

    for item in r[page - 1 * 20 : page * 20 - 1]:
        out.append(
            {
                "type": item[0],
                "author": item[1],
                "title": item[2],
                "icon": item[3],
                "url": item[4],
                "description": item[5],
                "ID": item[6],
                "category": item[7],
            }
        )

    conn.close()

    y = time.time()
    return {"count": len(out), "time": y - x, "result": out}


@projects.route("/", methods=["GET"])
def query():
    page = request.args.get("page", 1)
    request.args.get("sort", "updated")

    amount = 20 * int(page)

    # SQL stuff
    conn = sqlite3.connect(config.DATA + "data.db")
    r = conn.execute(
        f"select type, author, title, icon, url, description, rowid, category, uploaded, updated from projects where status = 'live' limit {amount}"
    ).fetchall()

    out = []

    for item in r[page - 1 * 20 : page * 20 - 1]:
        out.append(
            {
                "type": item[0],
                "author": item[1],
                "title": item[2],
                "icon": item[3],
                "url": item[4],
                "description": item[5],
                "ID": item[6],
                "category": item[7],
            }
        )

    conn.close()

    return {"count": len(out), "result": out}


@projects.route("/count")
def amount_of_projects():
    with open("./example_data.json", "r") as fp:
        x = json.loads(fp.read())
        amount = len(x)
        fp.close()
    return str(amount)


@projects.route("/id/<int:id>")
def get_proj(id):
    conn = sqlite3.connect(config.DATA + "data.db")

    this_user = util.authenticate(request.headers.get("Authorization"))

    if this_user == 32:
        return "Make sure authorization is basic!", 400
    elif this_user == 33:
        return "Token expired!", 429

    proj = conn.execute(
        f"select type, author, title, icon, url, description, rowid, category, status, uploaded, updated, body from projects where rowid = {id}"
    ).fetchone()

    conn.close()

    if not proj:
        return "Not found", 404

    if proj[8] != "live":
        if not this_user:
            return "Not found", 404
        if not proj[1] == this_user["id"]:
            return "Not found", 404

    return {
        "type": proj[0],
        "author": proj[1],
        "title": proj[2],
        "icon": proj[3],
        "url": proj[4],
        "description": proj[5],
        "ID": proj[6],
        "category": proj[7],
        "status": proj[8],
        "uploaded": proj[9],
        "updated": proj[10],
        "body": proj[11],
    }


@projects.route("/get/<string:slug>")
def get_project(slug: str):
    # connect to the thingy
    conn = sqlite3.connect(config.DATA + "data.db")

    # do we need auth? no
    # do we have auth? yes
    # this is an accurate representation of minecraft 1.15
    # auth:
    this_user = util.authenticate(request.headers.get("Authorization"))
    if this_user == 32:
        return "Make sure authorization is basic!", 400
    elif this_user == 33:
        return "Token expired!", 429

    # gimme dat project and gtfo
    proj = conn.execute(
        f"select type, author, title, icon, url, description, rowid, category, status, uploaded, updated, body from projects where url = '{util.sanitise(slug)}'"
    ).fetchone()
    conn.close()

    # hey u didn't give me a project, hate u
    if not proj:
        return "Not found", 404

    # shhh im a spy
    if proj[8] != "live":
        if this_user == 31:
            return "Not found", 404
        if not proj[1] == this_user["id"]:
            return "Not found", 404

    # alr fine I give up take the project
    return {
        "type": proj[0],
        "author": proj[1],
        "title": proj[2],
        "icon": proj[3],
        "url": proj[4],
        "description": proj[5],
        "ID": proj[6],
        "category": proj[7],
        "status": proj[8],
        "uploaded": proj[9],
        "updated": proj[10],
        "body": proj[11],
    }


@projects.route("/random")
def random():
    conn = sqlite3.connect(config.DATA + "data.db")
    proj = conn.execute(
        "SELECT type, author, title, icon, url, description, rowid, category, status, uploaded, updated, body FROM projects where status = 'live' ORDER BY RANDOM() LIMIT 1"
    ).fetchone()
    conn.close()
    return {
        "type": proj[0],
        "author": proj[1],
        "title": proj[2],
        "icon": proj[3],
        "url": proj[4],
        "description": proj[5],
        "ID": proj[6],
        "category": proj[7],
        "uploaded": proj[9],
        "updated": proj[10],
        "body": proj[11],
    }


@projects.route("/create", methods=["POST"])
def new_project():
    # Check authentication
    tok = request.headers.get("Authorization")

    if not tok:
        return "Not authenticated! You gotta log in first :P", 401

    user = util.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 33:
        return "Token expired!", 429

    banned = util.get_user_ban_data(user["id"])
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
    except:
        return "Missing field", 400

    if data["type"] not in config.valid_types:
        return f"Type {data['type']} is not a valid type! Acceptable content types: {config.valid_types}"

    if len(data["title"]) > 50:
        return "Title exceeds max length!", 400

    if len(data["description"]) > 200:
        return "Description exceeds max length", 400

    if not re.match(r'^[\w!@$()`.+,"\-\']{3,64}$', data["url"]):
        return "URL is bad", 400

    if "icon" in data:
        icon = files.upload_file(
            data["icon"],
            f"icons/{str(secrets.randbelow(999999))}.png",
            user["username"],
        )

    # Update database
    conn = sqlite3.connect(config.DATA + "data.db")

    if "icon" in data:
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
                        '{util.sanitise(data['type'])}', 
                        {user['id']}, 
                        '{util.sanitise(data['title'])}', 
                        '{util.sanitise(data['description'])}', 
                        '{util.sanitise(data['body'])}',
                        '{util.sanitise(data['category'])}', 
                        '{util.sanitise(data['url'])}', 
                        'draft',
                        {str(int( time.time() ))},
                        {str(int( time.time() ))},
                        {icon})"""
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
                        '{util.sanitise(data['type'])}', 
                        {user['id']}, 
                        '{util.sanitise(data['title'])}', 
                        '{util.sanitise(data['description'])}', 
                        '{util.sanitise(data['body'])}',
                        '{util.sanitise(data['category'])}', 
                        '{util.sanitise(data['url'])}', 
                        'draft',
                        {str(int( time.time() ))},
                        {str(int( time.time() ))})"""
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

    user = util.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 33:
        return "Token expired!", 429

    banned = util.get_user_ban_data(user["id"])
    if banned is not None:
        return {
            "banned": True,
            "reason": banned["reason"],
            "expires": banned["expires"],
        }, 403

    if not (util.user_owns_project(project=id, author=user["id"]) or user["role"] in ["admin","moderator"]):
        return "You don't have permission to edit this project. ", 403

    data = request.get_json(force=True)

    try:
        data["title"]
        data["description"]
        data["body"]
        data["category"]
    except:
        return "Missing field", 400

    if len(data["title"]) > 50:
        return "Title exceeds max length!", 400

    if len(data["description"]) > 200:
        return "Description exceeds max length", 400

    if "icon" in data:
        icon = files.upload_file(
            data["icon"],
            f"icons/{str(secrets.randbelow(999999))}.png",
            user["username"],
        )

    # Update database
    conn = sqlite3.connect(config.DATA + "data.db")

    try:
        if "icon" in data:
            conn.execute(
                f"""update projects set
                title = '{util.sanitise(data["title"])}',
                description = '{util.sanitise(data["description"])}',
                body = '{util.sanitise(data["body"])}',
                category = '{util.sanitise(data["category"])}',
                icon = '{icon}' 
                where rowid = {id}"""
            )
        else:
            conn.execute(
                f"""update projects set
                title = '{util.sanitise(data["title"])}',
                description = '{util.sanitise(data["description"])}',
                body = '{util.sanitise(data["body"])}',
                category = '{util.sanitise(data["category"])}' 
                where rowid = {id}"""
            )
    except:
        conn.rollback()
        util.post_error("Error updating project",traceback.format_exc())
        return "Something went wrong.", 500

    conn.commit()
    conn.close()
    
    if(user["role"] in ["admin","moderator"]):
        util.post_site_log(user["username"],"Edited project",f"Edited the project {data['title']}")

    return "done", 200
