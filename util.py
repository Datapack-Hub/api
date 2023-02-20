import sqlite3
import secrets

def get_user(id: int):
    conn = sqlite3.connect("data.db")
    
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
    conn = sqlite3.connect("data.db")
    
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
    conn = sqlite3.connect("data.db")
    
    # Select
    u = conn.execute(f"select token from users where github_id = {id}").fetchone()
    
    if not u:
        return None
    
    return u

def create_user_account(ghubdata: dict):
    conn = sqlite3.connect("data.db")
    
    token = secrets.token_urlsafe()
    # Create user entry in database
    conn.execute(f'INSERT INTO users (username, role, bio, github_id, token) VALUES ("{ghubdata["login"]}", "default", "A new Datapack Hub user!", {ghubdata["id"]}, "{token}")')
    
    conn.commit()
    conn.close()
    
    print(get_user_from_github_id(ghubdata["id"]))
    
    return token