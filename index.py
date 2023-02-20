import flask
from flask import request
import json
import sqlite3
import requests
import config
import util

app = flask.Flask("app")

@app.route("/")
def main():
    return "The API works!"

@app.route("/auth/login")
def login():
    return flask.redirect(f"https://github.com/login/oauth/authorize?client_id={config.github.client_id}")

@app.route("/auth/callback")
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
        
        resp = flask.make_response(flask.redirect("https://datapack-hub.pages.dev"))
        resp.set_cookie("token",t)
        
        return resp

# PROJECTS DATA
@app.route("/projects")
def projects():
    amount = request.args.get("amount", 20)
    sort = request.args.get("sort", "updated")
    
    # SQL stuff
    conn = sqlite3.connect("data.db")
    r = conn.execute(f"select type, author, title, icon, url from projects limit {amount}")
    
@app.route("/projects/count")
def amount_of_projects():
    with open("./example_data.json","r") as fp:
        x = json.loads(fp.read())
        amount = len(x)
        fp.close()
    return str(amount)

# USER DATA
@app.route("/user/<int:id>")
async def user(id):
    u = util.get_user(id)
    if not u:
        return "User does not exist", 400
    return util.get_user(id)

app.run()