import sqlite3
import config

def reset():
    connection = sqlite3.connect(config.db)
    
    # This is actually probably the worst idea I've ever had
    connection.execute("DROP TABLE projects")
    connection.execute("DROP TABLE users")
    connection.execute("DROP TABLE banned_users")

    # Projects Data
    connection.execute("""create table IF NOT EXISTS projects(
        type STRING NOT NULL, 
        author INT NOT NULL, 
        title STRING NOT NULL, 
        description STRING NOT NULL,
        body STRING NOT NULL, 
        icon STRING, 
        url STRING NOT NULL UNIQUE, 
        status STRING NOT NULL, 
        downloads INT DEFAULT 0, 
        tags STRING,
        uploaded INT NOT NULL,
        updated INT NOT NULL);
    """)

    connection.execute("insert into projects values ('datapack', 1, 'Realistic Item Drops', 'Drops Realsitc short', 'actually very long description', 'https://cdn.discordapp.com/attachments/723984082853298297/1076083669409730590/IMG_2434.png', 'realistic-item-drops', 'draft', 0, '[\"utility\"]', 0, 0);")

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