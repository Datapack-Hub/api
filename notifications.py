"""
**Notifications API endpoints**
"""

import flask
from flask_cors import CORS
from flask import Blueprint, request
import util
import json
import sqlite3
import config
import regex as re

notifs = Blueprint("notifications",__name__,url_prefix="/notifs")

@notifs.route("/")
def all():
    if not request.headers.get("Authorization"):
        return "Authorization required", 401
    
    usr = util.authenticate(request.headers.get("Authorization"))
    
    if usr == 32:
        return "Please make sure authorization type = Basic"
    
    if usr == 33:
        return "Token Expired", 498
    
    conn = sqlite3.connect(config.db)
    notifs = conn.execute(f"select rowid, message, description, read, type from notifs where user = {usr['id']} order by rowid desc limit 20").fetchall()

    res = []

    for i in notifs:
        res.append({
            "id":i[0],
            "message":i[1],
            "description":i[2],
            "read":i[3],
            "type":i[4]
        })
    
    # Mark as read
    for i in res:
        if i["read"] == False:
            conn.execute("UPDATE notifs SET read = True WHERE rowid = " + str(i["id"]))
    
    conn.commit()
    conn.close()

    return {
        "count":len(res),
        "result":res
    }

@notifs.route("/unread")
def unread():
    if not request.headers.get("Authorization"):
        return "Authorization required", 401
    
    usr = util.authenticate(request.headers.get("Authorization"))
    
    if usr == 32:
        return "Please make sure authorization type = Basic"
    
    if usr == 33:
        return "Token Expired", 498
    
    conn = sqlite3.connect(config.db)
    notifs = conn.execute(f"select rowid, message, description, read, type from notifs where user = {usr['id']} and read = 0 order by rowid desc").fetchall()

    res = []

    for i in notifs:
        res.append({
            "id":i[0],
            "message":i[1],
            "description":i[2],
            "read":i[3],
            "type":i[4]
        })

    return {
        "count":len(res),
        "result":res
    }

@notifs.route("/send/<int:target>", methods=["POST"])
def send(target):
    if not request.headers.get("Authorization"):
        return "Authorization required", 401
    
    usr = util.authenticate(request.headers.get("Authorization"))
    
    if usr == 32:
        return "Please make sure authorization type = Basic"
    
    if usr == 33:
        return "Token Expired", 498

    if not (usr["role"] in ["admin","developer","moderator","helper"]):
        return "You are not allowed to do this!", 403

    notifData = request.get_json(force=True)

    conn = sqlite3.connect(config.db)
    try:
        conn.execute(f"INSERT INTO notifs VALUES ('{notifData['message']}', '{notifData['description']}', False, {target}, '{notifData['type']}')")
    except sqlite3.Error as er:
        return "There was a proble: " ' '.join(er.args) , 500
    conn.commit()
    conn.close()
    return "Successfully warned user!", 200