"""
**Auth API Endpoints**
"""

import random
import secrets
import sqlite3
import time
from urllib.parse import quote

import flask
import requests
from flask import request

import config
import utilities.auth_utils
import utilities.get_user
from utilities import util

auth = flask.Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/login/github")
def login_gh():
    return flask.redirect(
        f"https://github.com/login/oauth/authorize?client_id={config.GitHub.client_id}&redirect_uri=https%3A%2F%2Fapi.datapackhub.net%2Fauth%2Fcallback%2Fgithub"
    )


@auth.route("/login/discord")
def login_dc():
    return flask.redirect(
        "https://discord.com/api/oauth2/authorize?client_id=1121129295868334220&redirect_uri=https%3A%2F%2Fapi.datapackhub.net%2Fauth%2Fcallback%2Fdiscord&response_type=code&scope=identify"
    )


@auth.route("/callback/github")
def callback_gh():
    # Get an access token
    code = request.args.get("code")
    access_token = requests.post(
        f"https://github.com/login/oauth/access_token?client_id={config.GitHub.client_id}&client_secret={config.GitHub.client_secret}&code={quote(code)}",
        headers={"Accept": "application/json"},
        timeout=180,
    ).json()

    access_token = access_token["access_token"]

    # Get github ID
    github = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=120,
    ).json()

    # Get DH user
    u = utilities.get_user.from_github_id(github["id"])

    if not u:
        # Make account
        t = util.create_user_account(github)

        response = flask.make_response(
            flask.redirect(f"https://datapackhub.net?login=1&token={t}")
        )

        return response
    t = utilities.auth_utils.get_user_token(github["id"])

    if not t:
        return (
            "Something went wrong, but I can't actually be bothered to figure out why this error would ever be needed, because we already check if the user exists. For that reason, just assume that you broke something and it can never be fixed.",
            500,
        )

    response = flask.make_response(
        flask.redirect(f"https://datapackhub.net?login=1&token={t}")
    )

    return response


@auth.route("/callback/discord")
def callback_dc():
    # Get an access token
    code = request.args.get("code")

    data = {
        "client_id": config.Discord.client_id,
        "client_secret": config.Discord.client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://api.datapackhub.net/auth/callback/discord",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    access_token = requests.post(
        "https://discord.com/api/v10/oauth2/token",
        data=data,
        headers=headers,
        timeout=10000,
    ).json()["access_token"]

    # Get discord ID
    discord = requests.get(
        "https://discord.com/api/v10/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=120,
    ).json()

    # Get DH user
    u = utilities.get_user.from_discord_id(discord["id"])

    if not u:
        # Make account

        token = secrets.token_urlsafe()

        conn = util.make_connection()
        check = util.exec_query(
            conn,
            "select username from users where username = :dis_uname;",
            dis_uname=discord["username"],
        ).all()
        if not check:
            username = discord["username"]
        else:
            username = discord["username"] + str(random.randint(1, 99999))

        util.exec_query(
            conn,
            'INSERT INTO users (username, role, bio, discord_id, token, profile_icon, join_date) VALUES (:username, "default", "A new Datapack Hub user!", :d_id, :token, :avatar, :join)',
            username=username,
            d_id=discord["id"],
            token=token,
            avatar=f"https://cdn.discordapp.com/avatars/{discord['id']}/{discord['avatar']}.png",
            join=time.time(),
        )

        response = flask.make_response(
            flask.redirect(f"https://datapackhub.net?login=1&token={token}")
        )

        conn.commit()
        

        return response
    t = utilities.auth_utils.get_user_token_from_discord_id(discord["id"])

    if not t:
        return (
            "Something went wrong, but I can't actually be bothered to figure out why this error would ever be needed, because we already check if the user exists. For that reason, just assume that you broke something and it can never be fixed.",
            500,
        )

    response = flask.make_response(
        flask.redirect(f"https://datapackhub.net?login=1&token={t}")
    )

    return response


@auth.route("/link/discord", methods=["put"])
def link_discord():
    code = request.args.get("code")
    if not code:
        return "Code required", 400

    # Get signed-in user
    if not request.headers.get("Authorization"):
        return "Authorization required", 400

    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic", 400
    if usr == 33:
        return "Token Expired", 401

    # Get discord user info
    data = {
        "client_id": config.Discord.client_id,
        "client_secret": config.Discord.client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://datapackhub.net/settings/discord",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    access_token = requests.post(
        "https://discord.com/api/v10/oauth2/token",
        data=data,
        headers=headers,
        timeout=10000,
    ).json()["access_token"]

    # Get discord ID
    discord_id = requests.get(
        "https://discord.com/api/v10/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=120,
    ).json()["id"]

    conn = util.make_connection()
    try:
        util.exec_query(
            conn,
            "update users set discord_id = :id where rowid = :user;",
            id=discord_id,
            user=usr.id,
        )
    except sqlite3.Error:
        conn.rollback()
        
        return "Something went wrong!", 500
    conn.commit()
    
    return "Discord linked!", 200


@auth.route("/link/github", methods=["put"])
def link_github():
    # Get an access token
    code = request.args.get("code")

    access_token = requests.post(
        quote(
            f"https://github.com/login/oauth/access_token?client_id={config.GitHub.client_id}&client_secret={config.GitHub.client_secret}&code={code}"
        ),
        headers={"Accept": "application/json"},
        timeout=180,
    ).json()

    access_token = access_token["access_token"]

    # Get signed-in user
    if not request.headers.get("Authorization"):
        return "Authorization required", 400

    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic", 400
    if usr == 33:
        return "Token Expired", 401

    # Get github ID
    github = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=120,
    ).json()

    conn = util.make_connection()
    try:
        util.exec_query(
            conn,
            "update users set github_id = :g_id where rowid = :id;",
            g_id=github["id"],
            id=usr.id,
        )
    except sqlite3.Error:
        conn.rollback()
        
        return "Something went wrong!", 500
    conn.commit()
    
    return "Discord linked!", 200
