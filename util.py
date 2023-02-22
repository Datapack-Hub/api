import sqlite3
import secrets
import config
import flask

def get_user(id: int):
    conn = sqlite3.connect(config.db)
    
    # Select
    u = conn.execute(f"select username, rowid, role, bio from users where rowid = {id}").fetchone()
    
    if not u:
        return None
    
    
    return {
        "username":u[0],
        "id":u[1],
        "role":u[2],
        "bio":u[3]
    }
    
def get_user_from_github_id(id: int):
    conn = sqlite3.connect(config.db)
    
    # Select
    u = conn.execute(f"select username, rowid, role, bio from users where github_id = {id}").fetchone()
    
    if not u:
        return None
    
    return {
        "username":u[0],
        "id":u[1],
        "role":u[2],
        "bio":u[3]
    }
    
def get_user_token(github_id: int):
    conn = sqlite3.connect(config.db)
    
    # Select
    u = conn.execute(f"select token from users where github_id = {github_id}").fetchone()
    
    if not u:
        return None
    
    return u[0]

def get_user_from_token(token: str):
    conn = sqlite3.connect(config.db)
    
    # Select
    u = conn.execute(f"select username, rowid, role, bio from users where token = '{token}'").fetchone()
    
    if not u:
        print("huh?")
        return None
    
    return {
        "username":u[0],
        "id":u[1],
        "role":u[2],
        "bio":u[3]
    }

def create_user_account(ghubdata: dict):
    conn = sqlite3.connect(config.db)
    
    token = secrets.token_urlsafe()
    # Create user entry in database
    conn.execute(f'INSERT INTO users (username, role, bio, github_id, token) VALUES ("{ghubdata["login"]}", "default", "A new Datapack Hub user!", {ghubdata["id"]}, "{token}")')
    
    conn.commit()
    conn.close()
    
    print(get_user_from_github_id(ghubdata["id"]))
    
    return token

def get_user_ban_data(id: int):
    conn = sqlite3.connect(config.db)
    
    banned_user = conn.execute("select reason, expires from banned_users where id = " + str(id)).fetchone()
    
    if not banned_user:
        return None
    
    return {
        "reason": banned_user[0],
        "expires": banned_user[1]
    }