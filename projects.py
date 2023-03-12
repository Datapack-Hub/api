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
    amount = request.args.get("amount", 20)
    sort = request.args.get("sort", "updated")
    
    # SQL stuff
    conn = sqlite3.connect(config.db)
    r = conn.execute(f"select type, author, title, icon, url, description, rowid, tags from projects where status = 'live' limit {amount}").fetchall()
    
    out = []
    
    for item in r:
        out.append({
            "type":item[0],
            "author":item[1],
            "title":item[2],
            "icon":item[3],
            "url":item[4],
            "description":item[5],
            "ID":item[6],
            "tags":json.loads(item[7])
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

@projects.route("/get/<int:id>")
def get_proj(id):
    conn = sqlite3.connect(config.db)
    
    this_user = util.get_user.from_token(request.headers.get("token"))
    
    proj = conn.execute(f"select type, author, title, icon, url, description, rowid, tags, status from projects where rowid = {id}").fetchone()
    
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
            "tags":json.loads(proj[7])
        }
    
@projects.route("/create",methods=["POST"])
def new_project():
    # Check authentication
    tok = request.cookies.get("token")
    
    if not tok:
        return "Not authenticated! You gotta log in first :P", 401
    
    user = util.get_user.from_token(tok)
    
    if not user:
        return "Error authenticating. Please log in again.", 401
    
    b = util.get_user_ban_data(user["id"])
    
    if b:
        return f"This user is banned: {b['reason']}.", 403
    
    data = request.get_json(force=True)
    if data["type"] == None or data["url"] == None or data["title"] == None or data["description"] == None or data["tags"] == None:
        return "Missing field", 400
    if not data["type"] in config.valid_types:
        return f"Type {data['type']} is not a valid type! Acceptable content types: {config.valid_types}"
    if not re.match(r'^[\w!@$()`.+,"\-\']{3,64}$',data["url"]):
        return "URL is bad", 400
    if len(data["tags"]) > 3:
        return "Too many tags", 400
    
    # Update databas
    conn = sqlite3.connect(config.db)
    conn.execute(f"insert into projects(type, author, title, description, tags, url, status) values ('{data['type']}', {user['id']}, '{data['title']}', '{data['description']}', 'TODO', '{data['url']}', 'draft')")
    x = conn.execute("SELECT rowid, type, author, title, description, tags, url, status FROM projects ORDER BY rowid DESC LIMIT 1").fetchone()
    conn.commit()
    conn.close()

    return {
        "id":x[0],
        "type":x[1],
        "author":x[2],
        "title":x[3],
        "description":x[4],
        "tags":x[5],
        "url":x[6],
        "status":x[7]
    }