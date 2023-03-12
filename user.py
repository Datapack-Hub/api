"""
**User API endpoints**
"""

import flask
from flask_cors import CORS
from flask import Blueprint, request
import sqlite3
import config

import util

user = Blueprint("user",__name__,url_prefix="/user")

CORS(user,supports_credentials=True)

# @user.after_request
# def after(resp):
#     header = resp.headers
#     header['Access-Control-Allow-Credentials'] = "true"
#     # Other headers can be added here if needed
#     return resp

@user.route("/<string:username>")
def get_user(username):
    u = util.get_user.from_username(username)
    if not u:
        return "User does not exist", 404
    return u

@user.route("/id/<int:id>")
def get_user_id(id):
    u = util.get_user.from_id(id)
    if not u:
        return "User does not exist", 404
    return u

@user.route("/me")
def me():
    print(request.cookies.lists)
    t = request.cookies.get("token")
    if not t:
        return "Authentication required", 401
    
    u = util.get_user.from_token(request.cookies.get("token"))
    
    if u == 37:
        return "Auth failed", 400
    
    return u

@user.route("/<int:id>/projects")
def user_projects(id):
    conn = sqlite3.connect(config.db)
    # Check if user is authenticated
    t = request.cookies.get("token")
    if t:
        if util.get_user.from_token(t)["id"] == id:
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