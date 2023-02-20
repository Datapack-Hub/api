"""
**Projects API endpoints**
"""

import flask
from flask import Blueprint, request
import util
import json
import sqlite3
import config

projects = Blueprint("projects",__name__,url_prefix="/projects")

@projects.route("/", methods=["GET"])
def query():
    amount = request.args.get("amount", 20)
    sort = request.args.get("sort", "updated")
    
    # SQL stuff
    conn = sqlite3.connect(config.db)
    r = conn.execute(f"select type, author, title, icon, url, description, rowid from projects limit {amount}").fetchall()
    
    out = []
    
    for item in r:
        out.append({
            "type":item[0],
            "author":item[1],
            "title":item[2],
            "icon":item[3],
            "url":item[4],
            "description":item[5],
            "ID":item[6]
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
    
    proj = conn.execute(f"select type, author, title, icon, url, description, rowid from projects where rowid = {id}").fetchone()
    
    return {
            "type":proj[0],
            "author":proj[1],
            "title":proj[2],
            "icon":proj[3],
            "url":proj[4],
            "description":proj[5],
            "ID":proj[6]
        }