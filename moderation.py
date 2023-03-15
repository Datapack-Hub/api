"""
**Moderation API endpoints**
"""

console_commands = [
    "sql",
    "select",
    "ban",
    "hello"
]

import flask
from flask_cors import CORS
from flask import Blueprint, request
import sqlite3
import config
import json
import difflib
import util

def auth(token: str, perm_levels: list[str]):
    if not token:
        return False
    
    user = util.authenticate(token)
    
    if user == 33:
        return 33
    
    if user["role"] not in perm_levels:
        return False
    return True

mod = Blueprint("mod",__name__,url_prefix="/moderation")

CORS(mod,supports_credentials=True)

@mod.route("/console", methods=["POST"])
def console():
    data = json.loads(request.data)
    
    full = data["command"]
    
    args = data["command"].split()
    del args[0]
    
    cmd = data["command"].split()[0]
    
    if cmd not in console_commands:
        closest = difflib.get_close_matches(cmd, console_commands)
        if len(closest) >= 1:
            return f"Error: Command {cmd} not found. Did you mean {closest[0]}?", 400
        else:
            return f"Error: Command {cmd} not found.", 400
        
    # Check user authentication status
    if not util.get_user.from_token(request.headers.get("Authorization")[6:]):
        return "hey u! sign in again plz (i am not hax)", 429
        
    if cmd == "sql":
        # Check auth
        if not auth(request.headers.get("Authorization"), ["admin"]):
            return "You do not have permission to run this command!"
        
        sql_command = full[3:]
        
        # Run SQLITE command
        try:
            conn = sqlite3.connect(config.db)
            conn.execute(sql_command)
            conn.commit()
            conn.close()
        except sqlite3.Error as error:
            return "SQL Error: " + (' '.join(error.args)), 400
        else:
            return "Processed SQL command!", 200
        
    elif cmd == "select":
        if not auth(request.cookies.get("token"), ["admin", "developer"]):
            return "You do not have permission to run this command!"
        
        sql_command = "SELECT " + full[7:]
        
        # Run SQLITE command
        try:
            print(sql_command)
            conn = sqlite3.connect(config.db)
            out = conn.execute(sql_command).fetchall()
            conn.commit()
            conn.close()
        except sqlite3.Error as error:
            return "SQL Error: " + (' '.join(error.args)), 400
        else:
            return json.dumps(out, indent=3).replace("\n","<br />"), 200
    elif cmd == "ban":
        if not args[0]:
            return "Missing username/UID!", 400
        x = None
        try:
            x = int(args[0])
        except:
            print(f"{args[0]} is not an ID, but probably a username.")
            
        if x:
            # TODO Ban them by their ID
            conn = sqlite3.connect(config.db)
            
            if args[1]:
                conn.execute(f"INSERT INTO banned_users(id, reason) VALUES ({x}, \"{' '.join(args[1:])}\")")
                return f"Banned {args[0]} for reason {' '.join(args[1:])}"
            else:
                conn.execute(f"INSERT INTO banned_users(id) VALUES ({x})")
                return f"Banned {args[0]}"
        else:
            # TODO Ban them by their username
            pass
        
        print(int(args[0]))
        return f"User: {args[0]} | Reason: {' '.join(args[1:])}"
    elif cmd == "hello":
        return "Beep boop! Hi!"
    
@mod.route("/get_members")
def members():
    # Check auth
    if not auth(request.headers.get("Authorization"), ["admin"]):
        return 403
    
    conn = sqlite3.connect(config.db)
    
    data = conn.execute("SELECT rowid, username, profile_icon, role, github_id FROM users").fetchall()
    
    return_this = ""
    
    for i in data:
        return_this = return_this + f'''<tr>
        <th scope="row">{i[0]}</th>
        <td><img class="smol" src="{i[2]}" />{i[1]}</td>
        <td>{i[3].capitalize()}</td>
        <td>{i[4]}</td>
        <td>
            <button id="logout" type="button" class="btn btn-danger btn-sm" onclick="logOutButton({i[0]})">Log Out</button>
            <button id="ban" type="button" class="btn btn-danger btn-sm" onclick="banButton({i[0]})">Ban</button>
        </td></tr>'''
        
        print(return_this)
        
    return {
        "result": return_this
    }
    
@mod.route("/moderate/<int:id>", methods=["post"])
def moderate(id):
    # Check auth
    if not auth(request.headers.get("Authorization"), ["admin","moderator","developer"]):
        return 403
    
    data = request.get_json(force=True)
    
    if data["action"] == "log_out":
        try:
            util.log_user_out(id)
        except:
            return "Failed", 500
        else:
            return "Success!", 200