import sqlite3
import config

def reset():
    connection = sqlite3.connect(config.db)

    # Projects Data
    connection.execute("""create table projects(
        type STRING NOT NULL, 
        author INT NOT NULL, 
        title STRING NOT NULL, 
        description STRING NOT NULL, 
        icon STRING, 
        url STRING NOT NULL UNIQUE, 
        status STRING NOT NULL, 
        downloads INT DEFAULT 0, 
        tags STRING);
    """)

    connection.execute("insert into projects values ('datapack', 1, 'Realistic Item Drops', 'Drops Realsitc', 'https://cdn.discordapp.com/attachments/723984082853298297/1076083669409730590/IMG_2434.png', 'realistic-item-drops', 'draft', 0, '[\"utility\"]');")

    # User data
    connection.execute("""create table IF NOT EXISTS users (
        username string NOT NULL UNIQUE, 
        token string NOT NULL UNIQUE, 
        role string NOT NULL, 
        bio STRING, 
        github_id int NOT NULL UNIQUE,
        profile_icon string NOT NULL
    )""")

    # Banned User Data
    connection.execute("""create table IF NOT EXISTS banned_users (
        id int NOT NULL UNIQUE,
        expires int,
        reason string
    )""")

    connection.commit()
        
    connection.close()
    
if __name__ == "__main__":
    reset()