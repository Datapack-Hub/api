"""
**User API endpoints**
"""

import flask
from flask import Blueprint, request
import sqlite3
import config

import util

user = Blueprint("user",__name__,url_prefix="/user")

@user.route("/<int:id>")
async def get_user(id):
    u = util.get_user(id)
    if not u:
        return "User does not exist", 400
    return util.get_user(id)

@user.route("/me")
def me():
    t = request.cookies.get("token")
    if not t:
        return "Authentication required", 401
    
    return util.get_user_from_token(request.cookies.get("token"))

@user.route("/<int:id>/projects")
async def user_projects(id):
    conn = sqlite3.connect(config.db)
    # Check if user is authenticated
    t = request.cookies.get("token")
    if t:
        if util.get_user_from_token(t)["id"] == id:
            # Get all submissions
            r = conn.execute(f"select type, author, title, icon, url, description, rowid from projects where author = {id} and status != 'deleted'").fetchall()
            
            # Form array
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
    else:
        # Get all PUBLIC submissions
        r = conn.execute(f"select type, author, title, icon, url, description, rowid from projects where author = {id} and status == 'live'").fetchall()
        
        # Form array
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