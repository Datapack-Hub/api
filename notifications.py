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

CORS(notifs)

@notifs.after_request
def after(resp):
    header = resp.headers
    header['Access-Control-Allow-Credentials'] = "true"
    # Other headers can be added here if needed
    return resp

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
    notifs = conn.execute(f"select (rowid, message, description, read) from notifs where user = {usr['id']} and read = 0").fetchall()

    res = []

    for i in notifs:
        res.append({
            "id":i[0],
            "message":i[1],
            "description":i[2],
            "read":i[3]
        })

    return {
        "count":len(res),
        "result":res
    }
