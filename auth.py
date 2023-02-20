"""
**Auth API Endpoints**
"""

import flask
import requests
import util
from flask import request
import config

auth = flask.Blueprint("auth",__name__,url_prefix="/auth")

@auth.route("/login")
def login():
    return flask.redirect(f"https://github.com/login/oauth/authorize?client_id={config.github.client_id}")

@auth.route("/callback")
def callback():
    # Get an access token
    code = request.args.get("code")
    access_token = requests.post(f"https://github.com/login/oauth/access_token?client_id={config.github.client_id}&client_secret={config.github.client_secret}&code={code}",headers={"Accept":"application/json"}).json()["access_token"]
    
    # Get github ID
    github = requests.get("https://api.github.com/user",headers={"Authorization":f"Bearer {access_token}"}).json()
    
    # Get DH user
    u = util.get_user_from_github_id(github["id"])
    
    if not u:
        # Make account
        print(github)
        t = util.create_user_account(github)
        
        resp = flask.make_response(flask.redirect("https://datapack-hub.pages.dev"))
        resp.set_cookie("token",t)
        
        return resp
    else:
        t = util.get_user_token(github["id"])
        
        if not t:
            return "Something went wrong, but I can't actually be bothered to figure out why this error would ever be needed, because we already check if the user exists. For that reason, just assume that you broke something and it can never be fixed."
        
        resp = flask.make_response(flask.redirect("https://datapack-hub.pages.dev"))
        
        print(t)
        resp.set_cookie("token",t)
        
        return resp