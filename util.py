import sqlite3
import secrets
import config
import flask
from hashlib import sha256

def authenticate(auth: str):
    """
    `dict` - If success returns user details\n
    `31` - If auth not supplied\n
    `32` - If auth is not basic\n
    `33` - If user is not existing\n
    """
    if not auth:
        return 31
    if not auth.startswith("Basic"):
        return 32
    
    token = auth[6:]
    
    conn = sqlite3.connect(config.db)
    u = conn.execute(f"select username, rowid, role, bio, profile_icon from users where token = '{token}'").fetchone()
    if not u:
        print("user doth not exists")
        return 33
    conn.close()
    
    return {
        "username":u[0],
        "id":u[1],
        "role":u[2],
        "bio":u[3],
        "profile_icon":u[4]
    }

class get_user():
    def from_username(uname: str):
        conn = sqlite3.connect(config.db)
    
        # Select
        u = conn.execute(f"select username, rowid, role, bio, profile_icon from users where lower(username) = '{uname.lower()}'").fetchone()
        
        if not u:
            return None
        
        conn.close()
        
        return {
            "username":u[0],
            "id":u[1],
            "role":u[2],
            "bio":u[3],
            "profile_icon":u[4]
        }
        
    def from_id(id: int):
        conn = sqlite3.connect(config.db)
    
        # Select
        u = conn.execute(f"select username, rowid, role, bio, profile_icon from users where rowid = {id}").fetchone()
        
        if not u:
            return None
        
        conn.close()
        
        return {
            "username":u[0],
            "id":u[1],
            "role":u[2],
            "bio":u[3],
            "profile_icon":u[4]
        }
        
    def from_github_id(id: int):
        conn = sqlite3.connect(config.db)
        
        # Select
        u = conn.execute(f"select username, rowid, role, bio, profile_icon from users where github_id = {id}").fetchone()
        
        if not u:
            return None
        
        conn.close()
            
        return {
            "username":u[0],
            "id":u[1],
            "role":u[2],
            "bio":u[3],
            "profile_icon":u[4]
        }
    def from_token(token: str):
        conn = sqlite3.connect(config.db)
    
        # Select
        u = conn.execute(f"select username, rowid, role, bio, profile_icon from users where token = '{token}'").fetchone()
        
        if not u:
            print("SillySilabearError: The user does not exist")
            return False
        
        conn.close()
        
        return {
            "username":u[0],
            "id":u[1],
            "role":u[2],
            "bio":u[3],
            "profile_icon":u[4]
        }
    
def get_user_token(github_id: int):
    conn = sqlite3.connect(config.db)
    
    # Select
    u = conn.execute(f"select token from users where github_id = {github_id}").fetchone()
    
    conn.close()
    
    if not u:
        return None
    
    return u[0]

def create_user_account(ghubdata: dict):
    conn = sqlite3.connect(config.db)
    
    token = secrets.token_urlsafe()
    
    # Create user entry in database
    conn.execute(f'INSERT INTO users (username, role, bio, github_id, token, profile_icon) VALUES ("{ghubdata["login"]}", "default", "A new Datapack Hub user!", {ghubdata["id"]}, "{token}", "{ghubdata["avatar_url"]}")')
    
    conn.commit()
    conn.close()
    
    print("CREATED USER: " + ghubdata["login"])
    
    return token

def get_user_ban_data(id: int):
    conn = sqlite3.connect(config.db)
    
    banned_user = conn.execute("select reason, expires from banned_users where id = " + str(id)).fetchone()
    
    if not banned_user:
        return None
    
    conn.close()
    
    return {
        "reason": banned_user[0],
        "expires": banned_user[1]
    }
    
def log_user_out(id: int):
    conn = sqlite3.connect(config.db)
    
    token = secrets.token_urlsafe()
    
    # Create user entry in database
    try:
        conn.execute(f'UPDATE users SET token = "{token}" WHERE rowid = {id}')
    except sqlite3.Error as err:
        return err
    
    conn.commit()
    conn.close()
    
    return "Success!"

def update_user(username: str):
    pass