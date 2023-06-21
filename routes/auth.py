"""
**Auth API Endpoints**
"""

import flask
import requests
import usefuls.util as util
from flask import request
import config
import sqlite3
import secrets

auth = flask.Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/login/github")
def login_gh():
    return flask.redirect(
        f"https://github.com/login/oauth/authorize?client_id={config.github.client_id}"
    )


@auth.route("/login/discord")
def login_dc():
    return flask.redirect(
        f"https://discord.com/oauth2/authorize?client_id=1121129295868334220&redirect_uri=https%3A%2F%2Fapi.datapackhub.net%2Fauth%2Fdiscord%2Fcallback&response_type=code&scope=identify"
    )


@auth.route("/callback/github")
def callback_gh():
    # Get an access token
    code = request.args.get("code")
    access_token = requests.post(
        f"https://github.com/login/oauth/access_token?client_id={config.github.client_id}&client_secret={config.github.client_secret}&code={code}",
        headers={"Accept": "application/json"},
        timeout=180,
    ).json()["access_token"]

    # Get github ID
    github = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=120,
    ).json()

    # Get DH user
    u = util.get_user.from_github_id(github["id"])

    if not u:
        # Make account
        t = util.create_user_account(github)

        resp = flask.make_response(
            flask.redirect(f"https://datapackhub.net?login=1&token={t}")
        )

        return resp
    else:
        t = util.get_user_token(github["id"])

        if not t:
            return (
                "Something went wrong, but I can't actually be bothered to figure out why this error would ever be needed, because we already check if the user exists. For that reason, just assume that you broke something and it can never be fixed.",
                500,
            )

        resp = flask.make_response(
            flask.redirect(f"https://datapackhub.net?login=1&token={t}")
        )

        return resp


@auth.route("/callback/discord")
def callback_dc():
    # Get an access token
    access_token = request.args.get("access_token")

    # Get discord ID
    discord = requests.get(
        "https://discord.com/api/oauth2/@me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=120,
    ).json()["user"]

    # Get DH user
    u = util.get_user.from_github_id(discord["id"])

    if not u:
        # Make account
        conn = sqlite3.connect(config.DATA + "data.db")

        token = secrets.token_urlsafe()
        conn.execute(
            f'INSERT INTO users (username, role, bio, discord_id, token, profile_icon) VALUES ("{discord["username"]}", "default", "A new Datapack Hub user!", {discord["id"]}, "{token}", "https://cdn.discordapp.com/avatars/{discord["id"]}/{discord["avatar"]}.png")'
        )

        resp = flask.make_response(
            flask.redirect(f"https://datapackhub.net?login=1&token={t}")
        )

        return resp
    else:
        t = util.get_user_token_from_discord_id(discord["id"])

        if not t:
            return (
                "Something went wrong, but I can't actually be bothered to figure out why this error would ever be needed, because we already check if the user exists. For that reason, just assume that you broke something and it can never be fixed.",
                500,
            )

        resp = flask.make_response(
            flask.redirect(f"https://datapackhub.net?login=1&token={t}")
        )

        return resp
