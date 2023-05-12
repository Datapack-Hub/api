"""
**Versions API endpoints**
"""

from flask_cors import CORS
from flask import Blueprint, request
import util
import sqlite3
import config
import files

versions = Blueprint("versions", __name__, url_prefix="/versions")

CORS(versions)


@versions.route("/project/<int:id>")
def project(id: int):
    # Select all versions where the project is this one
    conn = sqlite3.connect(f"{config.DATA}data.db")
    v = conn.execute(f"SELECT * FROM versions WHERE project = {str(id)}").fetchall()
    out = []
    for i in v:
        o = {
            "name": i[0],
            "description": i[1],
            "primary_download": i[2],
            "minecraft_versions": i[4],
            "version_code": i[5],
        }

        if i[3] != None:
            o["resource_pack_download"]: i[3]

        out.append(o)

    return {"count": len(out), "result": out}


@versions.route("/project/<int:id>/<string:code>")
def code(id: int, code: str):
    # Select all versions where the project is this one
    conn = sqlite3.connect(f"{config.DATA}data.db")
    v = conn.execute(
        f"SELECT * FROM versions WHERE version_code = '{code}' AND project = {id}"
    ).fetchone()

    return {
        "name": v[0],
        "description": v[1],
        "primary_download": v[2],
        "minecraft_versions": v[4],
        "version_code": v[5],
    }


@versions.route("/new/<int:project>", methods=["post"])
def new(project: int):
    # Authenticate user
    usr = util.authenticate(request.headers.get("Authorization"))
    if usr == 32:
        return "Please make sure authorization type = Basic"
    if usr == 33:
        return "Token Expired", 498

    # Check if user is banned
    banned = util.get_user_ban_data(usr["id"])

    if banned:
        return {
            "banned": True,
            "reason": banned["reason"],
            "expires": banned["expires"],
        }, 403

    # Check if user is the owner of project
    if not util.user_owns_project(usr["id"], project):
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

        dpath = files.upload_file(
            data["primary_download"],
            f"project/{project}/{data['version_code']}/{data['filename']}",
            usr["username"],
        )
        try:
            data["resource_pack_download"]
        except:
            conn.execute(
                f"INSERT INTO versions(name,description,primary_download,minecraft_versions,version_code,project) VALUES ('{data['name']}', '{data['description']}', '{dpath}','{','.join(data['minecraft_versions'])}', '{data['version_code']}', {str(project)})"
            )
        else:
            if data["resource_pack_download"] is not None:
                rpath = files.upload_file(
                    data["resource_pack_download"],
                    f"project/{project}/{data['version_code']}/{data['filename']}",
                    usr["username"],
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

    conn.commit()
    conn.close()

    return o