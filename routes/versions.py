"""
**Versions API endpoints**
"""

import sqlite3
import time
from urllib.parse import quote

from flask import Blueprint, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequestKeyError

import utilities.auth_utils
from utilities import files, util

versions = Blueprint("versions", __name__, url_prefix="/versions")

CORS(versions)


@versions.route("/project/<int:id>")
def project(id: int):
    # Select all versions where the project is this one
    conn = util.make_connection()
    v = util.exec_query(
        conn, "SELECT * FROM versions WHERE project = :pid ORDER BY rowid DESC", pid=id
    ).all()
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
    conn = util.make_connection()
    # Get the project
    p = util.exec_query(
        conn, "SELECT rowid FROM projects WHERE url = :url;", url=id
    ).all()
    if not p:
        return "Project not found", 404

    # Select all versions where the project is this one
    v = util.exec_query(
        conn,
        "SELECT * FROM versions WHERE project = :id ORDER BY rowid DESC",
        id=p[0][0],
    ).all()
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
            return "You need to be signed in!", 401
        elif usr == 32:
            return "Make sure authorization is basic!", 400
        elif usr == 33:
            return "Token expired!", 401

        if util.user_owns_project(id, usr.id):
            conn = util.make_connection()
            try:
                util.exec_query(
                    conn,
                    "DELETE FROM versions WHERE version_code = :code AND project = :id",
                    code=code,
                    id=id,
                )
            except sqlite3.Error:
                conn.rollback()
                conn.close()
                return "There was an error deleting that version!", 500
            else:
                conn.commit()
                conn.close()
                return "didded", 200
        else:
            return "Not your version! :P", 403
    else:
        # Select all versions where the project is this one
        conn = util.make_connection()
        v = util.exec_query(
            conn,
            "SELECT * FROM versions WHERE version_code = :code AND project = :id ORDER BY rowid DESC",
            code=code,
            id=id,
        ).one_or_none()

        try:
            v[0]
        except:
            return "Not found.", 404

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

    if banned is not None:
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

    try:
        data["name"]
        data["description"]
        data["minecraft_versions"]
        data["version_code"]
        data["primary_download"]
        data["filename"]
    except BadRequestKeyError as ex:
        return f"Error:  {' '.join(ex.args)}"
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

        sq = bool("squash" in data and data["squash"] is True)

        dpath = files.upload_zipfile(
            data["primary_download"],
            f"project/{project}/{quote(data['version_code'])}/{quote(data['filename'])}",
            usr.username,
            sq,
        )

        sorted_versions = sorted(data["minecraft_versions"], key=util.custom_sort_key)

        try:
            data["resource_pack_download"]
        except BadRequestKeyError:
            util.commit_query(
                """INSERT INTO versions(
                        name,
                        description,
                        primary_download,
                        minecraft_versions,
                        version_code,
                        project
                    ) VALUES (:name, :desc, :path, :mcv, :vc, :project)""",
                name=data["name"],
                desc=data["description"],
                path=dpath,
                mcv=",".join(sorted_versions),
                vc=data["version_code"],
                project=project,
            )
        else:
            if data["resource_pack_download"] != "":
                rpath = files.upload_zipfile(
                    data["resource_pack_download"],
                    f"project/{project}/{quote(data['version_code'])}/resourcepack-{quote(data['filename'])}",
                    usr.username,
                )
                util.commit_query(
                    """INSERT INTO versions(
                            name,
                            description,
                            primary_download,
                            resource_pack_download,
                            minecraft_versions,
                            version_code,
                            project
                        ) VALUES (:name, :desc, :dpath, :rpath, :mcv, :vc, :project)""",
                    name=data["name"],
                    desc=data["description"],
                    dpath=dpath,
                    rpath=rpath,
                    mcv=",".join(sorted_versions),
                    vc=data["version_code"],
                    project=project,
                )
            else:
                util.commit_query(
                    """INSERT INTO versions(
                            name,
                            description,
                            primary_download,
                            minecraft_versions,
                            version_code,
                            project
                        ) VALUES (:name, :desc, :path,:mcv, :vc, :project)""",
                    name=data["name"],
                    desc=data["description"],
                    path=dpath,
                    mcv=",".join(data["minecraft_versions"]),
                    vc=data["version_code"],
                    project=project,
                )

    conn = util.make_connection()
    v = util.exec_query(
        conn, "SELECT * FROM versions WHERE version_code = :vc", vc=data["version_code"]
    ).one()

    o = {
        "name": v[0],
        "description": v[1],
        "primary_download": v[2],
        "minecraft_versions": v[4],
        "version_code": v[5],
    }

    if v[3] is not None:
        o["resource_pack_download"] = v[3]

    util.exec_query(
        conn,
        "update projects set updated = :updated where rowid = :id;",
        updated=str(int(time.time())),
        id=project,
    )
    conn.commit()
    conn.close()

    return o
