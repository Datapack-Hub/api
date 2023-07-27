"""
**Versions API endpoints**
"""

import sqlite3
import time

from flask import Blueprint, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequestKeyError

import config
import utilities.auth_utils
import utilities.files as files
import utilities.util as util

versions = Blueprint("versions", __name__, url_prefix="/versions")

CORS(versions)


@versions.route("/project/<int:id>")
def project(id: int):
    # Select all versions where the project is this one
    conn = sqlite3.connect(f"{config.DATA}data.db")
    v = conn.execute(
        f"SELECT * FROM versions WHERE project = {str(id)} ORDER BY rowid DESC"
    ).fetchall()
    out = []
    for i in v:
        o = {
            "name": i[0],
            "description": i[1],
            "primary_download": i[2],
            "minecraft_versions": i[4],
            "version_code": i[5],
        }

        if i[3] is not None:
            o["resource_pack_download"] = i[3]

        out.append(o)

    return {"count": len(out), "result": out}


@versions.route("/project/url/<string:id>")
def project_from_str(id: str):
    conn = sqlite3.connect(f"{config.DATA}data.db")
    # Get the project
    p = conn.execute(
        f"SELECT rowid FROM projects WHERE url = '{util.clean(id)}';"
    ).fetchall()
    if len(p) == 0:
        return "Project not found", 404

    # Select all versions where the project is this one
    v = conn.execute(
        f"SELECT * FROM versions WHERE project = {p[0][0]} ORDER BY rowid DESC"
    ).fetchall()
    out = []
    for i in v:
        o = {
            "name": i[0],
            "description": i[1],
            "primary_download": i[2],
            "minecraft_versions": i[4],
            "version_code": i[5],
        }

        if i[3] is not None:
            o["resource_pack_download"] = i[3]

        out.append(o)

    return {"count": len(out), "result": out}


@versions.route("/project/<int:id>/<string:code>", methods=["GET", "DELETE"])
def code(id: int, code: str):
    if request.method == "DELETE":
        usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
        if usr == 31:
            return "You need to be signed in!"
        elif usr == 32:
            return "Make sure authorization is basic!", 400
        elif usr == 33:
            return "Token expired!", 401

        if util.user_owns_project(id, usr.id):
            conn = sqlite3.connect(f"{config.DATA}data.db")
            try:
                conn.execute(
                    f"DELETE FROM versions WHERE version_code = '{code}' AND project = {id}"
                ).fetchone()
            except sqlite3.Error:
                return "There was an error deleting that version!", 500
            else:
                conn.commit()
                conn.close()
                return "didded", 200
        else:
            return "Not your version! :P", 403
    else:
        # Select all versions where the project is this one
        conn = sqlite3.connect(f"{config.DATA}data.db")
        v = conn.execute(
            f"SELECT * FROM versions WHERE version_code = '{code}' AND project = {id} ORDER BY rowid DESC"
        ).fetchone()

        o = {
            "name": v[0],
            "description": v[1],
            "primary_download": v[2],
            "minecraft_versions": v[4],
            "version_code": v[5],
        }

        if v[3] is not None:
            o["resource_pack_download"] = v[3]

        return o


@versions.route("/new/<int:project>", methods=["post"])
def new(project: int):
    # Authenticate user
    usr = utilities.auth_utils.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic", 400
    if usr == 33:
        return "Token Expired", 401

    # Check if user is banned
    banned = util.get_user_ban_data(usr.id)

    if banned:
        return {
            "banned": True,
            "reason": banned["reason"],
            "expires": banned["expires"],
        }, 403

    # Check if user is the owner of project
    if not util.user_owns_project(project=project, author=usr.id):
        return "You don't have permission to create a version on this project", 403

    # now do the stuff
    data = request.get_json(force=True)
    conn = sqlite3.connect(f"{config.DATA}data.db")

    try:
        data["name"]
        data["description"]
        data["minecraft_versions"]
        data["version_code"]
        data["primary_download"]
        data["filename"]
    except BadRequestKeyError as ex:
        return "Error: " + " ".join(ex.args)
    except:
        return (
            "Make sure you provide name, description, minecraft_versions, version_code, primary_download, filename and optionally resource_pack_download",
            400,
        )
    else:
        if len(data["name"]) > 50:
            return "Name is too long", 400

        if len(data["description"]) > 2000:
            return "Description is too long", 400

        if len(data["version_code"]) > 15:
            return "Version code too long", 400

        if "squash" in data:
            if data["squash"] is True:
                sq = True
            else:
                sq = False
        else:
            sq = False

        dpath = files.upload_zipfile(
            data["primary_download"],
            f"project/{project}/{data['version_code']}/{data['filename']}",
            usr.username,
            sq,
        )
        try:
            data["resource_pack_download"]
        except BadRequestKeyError:
            conn.execute(
                f"INSERT INTO versions(name,description,primary_download,minecraft_versions,version_code,project) VALUES ('{data['name']}', '{data['description']}', '{dpath}','{','.join(data['minecraft_versions'])}', '{data['version_code']}', {str(project)})"
            )
        else:
            if (data["resource_pack_download"] is not None) and (
                data["resource_pack_download"] != ""
            ):
                rpath = files.upload_zipfile(
                    data["resource_pack_download"],
                    f"project/{project}/{data['version_code']}/Resourcepack-{data['filename']}",
                    usr.username,
                )
                conn.execute(
                    f"INSERT INTO versions(name,description,primary_download,resource_pack_download,minecraft_versions,version_code,project) VALUES ('{data['name']}', '{data['description']}', '{dpath}','{rpath}','{','.join(data['minecraft_versions'])}', '{data['version_code']}', {str(project)})"
                )
            else:
                conn.execute(
                    f"INSERT INTO versions(name,description,primary_download,minecraft_versions,version_code,project) VALUES ('{data['name']}', '{data['description']}', '{dpath}','{','.join(data['minecraft_versions'])}', '{data['version_code']}', {str(project)})"
                )

    v = conn.execute(
        f"SELECT * FROM versions WHERE version_code = '{data['version_code']}'"
    ).fetchone()

    o = {
        "name": v[0],
        "description": v[1],
        "primary_download": v[2],
        "minecraft_versions": v[4],
        "version_code": v[5],
    }

    if v[3] is not None:
        o["resource_pack_download"]: v[3]

    conn.execute(
        f"update projects set updated = {str(int(time.time()))} where rowid = {project};"
    )

    conn.commit()
    conn.close()

    return o
