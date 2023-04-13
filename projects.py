"""
**Projects API endpoints**
"""

import flask
from flask_cors import CORS
from flask import Blueprint, request
import util
import json
import sqlite3
import config
import regex as re
import time

projects = Blueprint("projects",__name__,url_prefix="/projects")

CORS(projects)

@projects.after_request
def after(resp):
    header = resp.headers
    header['Access-Control-Allow-Credentials'] = "true"
    # Other headers can be added here if needed
    return resp

@projects.route("/", methods=["GET"])
def query():
    page = request.args.get("page", 1)
    sort = request.args.get("sort", "updated")
    
    amount = 20*page
    
    # SQL stuff
    conn = sqlite3.connect(config.db)
    r = conn.execute(f"select type, author, title, icon, url, description, rowid, tags, uploaded, updated from projects where status = 'live' limit {amount}").fetchall()
    
    out = []
    
    for item in r[-20:]:
        out.append({
            "type":item[0],
            "author":item[1],
            "title":item[2],
            "icon":item[3],
            "url":item[4],
            "description":item[5],
            "ID":item[6],
            "category":proj[7]
        })
    
    conn.close()
        
    return {
        "count":len(out),
        "result":out
    }
    
@projects.route("/count")
def amount_of_projects():
    with open("./example_data.json","r") as fp:
        x = json.loads(fp.read())
        amount = len(x)
        fp.close()
    return str(amount)

@projects.route("/id/<int:id>")
def get_proj(id):
    conn = sqlite3.connect(config.db)
    
    this_user = util.authenticate(request.headers.get("Authorization"))
    
    if this_user == 32:
        return "Make sure authorization is basic!", 400
    elif this_user == 33:
        return "Token expired!",429
    
    proj = conn.execute(f"select type, author, title, icon, url, description, rowid, tags, status, uploaded, updated, body from projects where rowid = {id}").fetchone()
    
    conn.close()
    
    if not proj:
        return "Not found", 404
    
    if proj[8] != "live":
        if not this_user:
            return "Not found", 404
        if not proj[1] == this_user["id"]:
            return "Not found", 404
    
    return {
            "type":proj[0],
            "author":proj[1],
            "title":proj[2],
            "icon":proj[3],
            "url":proj[4],
            "description":proj[5],
            "ID":proj[6],
            "category":proj[7],
            "uploaded":proj[9],
            "updated":proj[10],
            "body":proj[11]
        }

    
@projects.route("/get/<string:slug>")
def get_project(slug: str):
    # connect to the thingy thingy
    conn = sqlite3.connect(config.db)
    
    # do we need auth? no
    # do we have auth? yes
    # this is an accurate representation of minecraft 1.15
    # auth:
    this_user = util.authenticate(request.headers.get("Authorization"))
    if this_user == 32:
        return "Make sure authorization is basic!", 400
    elif this_user == 33:
        return "Token expired!",429
    
    # gimme dat project and gtfo
    proj = conn.execute(f"select type, author, title, icon, url, description, rowid, tags, status, uploaded, updated, body from projects where url = '{slug}'").fetchone()
    conn.close()
    
    # hey u didnt give me a project, hate u
    if not proj:
        return "Not found", 404
    
    # shh im a spy
    if proj[8] != "live":
        if not this_user:
            return "Not found", 404
        if not proj[1] == this_user["id"]:
            return "Not found", 404
    
    # alr fine i give up take the project
    return {
            "type":proj[0],
            "author":proj[1],
            "title":proj[2],
            "icon":proj[3],
            "url":proj[4],
            "description":proj[5],
            "ID":proj[6],
            "category":proj[7],
            "uploaded":proj[9],
            "updated":proj[10],
            "body":proj[11]
        }
    
@projects.route("/create",methods=["POST"])
def new_project():
    # Check authentication
    tok = request.headers.get("Authorization")
    
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401
    
    user = util.authenticate(tok)
    if user == 32:
        return "Make sure authorization is basic!", 400
    elif user == 33:
        return "Token expired!",429
    
    banned = util.get_user_ban_data(user["id"])
    if banned != None:
        return {
            "banned":True,
            "reason":banned["reason"],
            "expires":banned["expires"]
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
    
    if not data["type"] in config.valid_types:
        return f"Type {data['type']} is not a valid type! Acceptable content types: {config.valid_types}"
    
    if not re.match(r'^[\w!@$()`.+,"\-\']{3,64}$',data["url"]):
        return "URL is bad", 400
    
    # Update databas
    conn = sqlite3.connect(config.db)
    conn.execute(f"""insert into projects(
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
                    '{data['type']}', 
                    {user['id']}, 
                    '{data['title']}', 
                    '{data['description']}', 
                    '{data['body']}',
                    '{data['category']}', 
                    '{data['url']}', 
                    'draft',
                    {str(round(time.time()))},
                    {str(round(time.time()))})""")
    conn.commit()
    conn.close()

    return "done", 200