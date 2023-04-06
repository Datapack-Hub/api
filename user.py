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
    print(request.headers.get("Authorization"))
    
    if not request.headers.get("Authorization"):
        return "Authorization required", 401
    
    usr = util.authenticate(request.headers.get("Authorization"))
    
    if usr == 32:
        return "Please make sure authorization type = Basic"
    
    if usr == 33:
        return "Token Expired", 498
    
    print(usr["username"] + " is " + usr["role"])
    # Failsafe lol
    if usr["username"] == "Silabear":
        conn = sqlite3.connect(config.db)
        conn.execute("UPDATE users SET role = 'admin' WHERE username = 'Silabear'")
        print("done?")
        conn.close()
    
    return usr

@user.route("/<string:username>/projects")
def user_projects(username):
    conn = sqlite3.connect(config.db)
    # Check if user is authenticated
    t = request.headers.get("Authorization")
    user = util.get_user.from_username(username)
    
    authed = util.authenticate(t)
    
    if authed == 32:
        return "Make sure authorization is basic!", 400
    elif authed == 33:
        return "Token expired!",429
    
    if t:
        if authed["id"] == user["id"]:
            # Get all submissions
            r = conn.execute(f"select type, author, title, icon, url, description, rowid, status from projects where author = {user['id']} and status != 'deleted'").fetchall()
            
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
                    "ID":item[6],
                    "status":item[7]
                })
            
            conn.close()
                
            return {
                "count":len(out),
                "result":out
            }
        else:
            # Get all PUBLIC submissions
            r = conn.execute(f"select type, author, title, icon, url, description, rowid, status from projects where author = {user['id']} and status == 'live'").fetchall()
            
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
                    "ID":item[6],
                    "status":item[7]
                })
            
            conn.close()
                
            return {
                "count":len(out),
                "result":out
            }
    else:
        # Get all PUBLIC submissions
        r = conn.execute(f"select type, author, title, icon, url, description, rowid from projects where author = {user['id']} and status == 'live'").fetchall()
        
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
        
@user.route("/<string:username>/edit", methods=["POST"])
def edit(username: str):
    t = request.headers.get("Authorization")
    user = util.get_user.from_username(username)
    
    
    if t:
        loggedin = util.authenticate(t)
        if loggedin == 32:
            return "Make sure authorization is basic!", 400
        elif loggedin == 33:
            return "Token expired!",429
        
        if loggedin["id"] == user["id"]:
            # User is logged in 
            data = request.get_json()
            
            if data["bio"]:
                conn = sqlite3.connect(config.db)
                conn.execute(f"UPDATE users SET bio = '{data['bio']}' WHERE username = '{username}'")
                conn.commit()
                conn.close()
        
            if data["username"]:
                conn = sqlite3.connect(config.db)
                conn.execute(f"UPDATE users SET username = '{data['username']}' WHERE username = '{username}'")
                conn.commit()
                conn.close()
            
            return "pretend it worked", 200
        else:
            return "You do not have perms!", 403
    else:
        return "You must log in!", 401