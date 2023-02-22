"""
**Projects API endpoints**
"""

import flask
from flask import Blueprint, request
import util
import json
import sqlite3
import config
import regex as re

projects = Blueprint("projects",__name__,url_prefix="/projects")

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
    
    proj = conn.execute(f"select type, author, title, icon, url, description, rowid, tags from projects where rowid = {id}").fetchone()
    
    conn.close()
    
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
    user = util.get_user_from_token(tok)
    b = util.get_user_ban_data(user["id"])
    if b:
        return f"This user is banned: {b['reason']}.", 403
    data = request.get_json(force=True)
    if not data["type"] or not data["url"] or not data["title"] or not data["description"] or not data["tags"] or not data["icon"] or not data["gallery"]:
        return "Missing field", 400
    if not data["type"] in config.valid_types:
        return f"Type {json['type']} is not a valid type! Acceptable content types: {config.valid_types}"
    if not re.match(r'^[\w!@$()`.+,"\-\']{3,64}$',json["url"]):
        return "URL is bad", 400
    if len(data["tags"]) > 3:
        return "Too many tags", 400
    
    # Update database
    conn = sqlite3.connect(config.db)
    
    conn.execute("insert into projects(type, author, title, description)")