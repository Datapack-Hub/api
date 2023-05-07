import sqlite3
import config


def reset(table: str):
    connection = sqlite3.connect(config.DATA + "data.db")

    if table != "no-drop":
        connection.execute(f"DROP TABLE {table}")

    # Projects Data
    connection.execute(
        """create table IF NOT EXISTS projects(
        type STRING NOT NULL, 
        author INT NOT NULL, 
        title STRING NOT NULL, 
        description STRING NOT NULL,
        body STRING NOT NULL, 
        icon STRING, 
        url STRING NOT NULL UNIQUE, 
        status STRING NOT NULL DEFAULT "draft", 
        category STRING NOT NULL,
        uploaded INT NOT NULL,
        updated INT NOT NULL);
    """
    )

    if table == "projects":
        connection.execute(
            "insert into projects values ('datapack', 1, 'Realistic Item Drops', 'Drops Realsitc short', 'actually very long description', 'https://cdn.discordapp.com/attachments/723984082853298297/1076083669409730590/IMG_2434.png', 'realistic-item-drops', 'live', 0, '[\"utility\"]', 0, 0);"
        )

    # Versions Data
    connection.execute(
        """create table if not exists versions(
        name STRING NOT NULL,
        description STRING NOT NULL,
        primary_download STRING NOT NULL,
        resource_pack_download STRING,
        minecraft_versions STRING NOT NULL,
        version_code STRING NOT NULL,
        project INT NOT NULL
    );
    """
    )

    # User data
    connection.execute(
        """create table IF NOT EXISTS users (
        username string NOT NULL UNIQUE, 
        token string NOT NULL UNIQUE, 
        role string NOT NULL, 
        bio STRING, 
        github_id int NOT NULL UNIQUE,
        profile_icon string NOT NULL
    )"""
    )

    # Banned User Data
    connection.execute(
        """create table IF NOT EXISTS banned_users (
        id int NOT NULL UNIQUE,
        expires int,
        reason string
    )"""
    )

    # Notification Data
    connection.execute(
        """create table if not exists notifs(
        message STRING NOT NULL,
        description STRING NOT NULL,
        read BOOL NOT NULL,
        type STRING NOT NULL,
        project INT NOT NULL
    );
    """
    )

    # save and exit
    connection.commit()
    connection.close()


if __name__ == "__main__":
    reset("no-drop")

    conn = sqlite3.connect(config.DATA + "data.db")
    print(
        conn.execute(
            "select * from projects where url = 'realistic-item-drops'"
        ).fetchone()
    )
