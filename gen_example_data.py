import sqlite3

import config


def reset(table: str):
    connection = sqlite3.connect(config.DATA + "data.db")

    if table != "no-drop":
        connection.execute(f"DROP TABLE {table}")

    # SQLite optimizations
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA mmap_size = 1000000000")

    # ! This operation may not be supported, disable if you run into issues
    connection.execute("PRAGMA journal_mode = WAL")

    # Projects Data
    connection.execute(
        """CREATE TABLE \"projects\"(
            type TEXT NOT NULL,
            author INT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            body TEXT NOT NULL,
            icon TEXT,
            url TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT \"draft\",
            category TEXT NOT NULL,
            uploaded INT NOT NULL,
            updated INT NOT NULL,
            mod_message TEXT,
            downloads INT NOT NULL DEFAULT 0, 
            featured_until INT, 
            licence TEXT, 
            dependencies TEXT)
    """
    )

    # Versions Data
    connection.execute(
        """CREATE TABLE IF NOT EXISTS versions(
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        primary_download TEXT NOT NULL,
        resource_pack_download TEXT,
        minecraft_versions TEXT NOT NULL,
        version_code TEXT NOT NULL,
        project INT NOT NULL
    );
    """
    )

    # User data
    connection.execute(
        """CREATE TABLE IF NOT EXISTS users (
        username TEXT NOT NULL UNIQUE, 
        token TEXT NOT NULL UNIQUE, 
        role TEXT NOT NULL, 
        bio TEXT, 
        github_id int UNIQUE,
        discord_id int UNIQUE,
        badges TEXT,
        profile_icon TEXT NOT NULL
    )"""
    )

    # Banned User Data
    connection.execute(
        """CREATE TABLE IF NOT EXISTS banned_users (
        id int NOT NULL UNIQUE,
        expires int,
        reason TEXT
    )"""
    )

    # Notification Data
    connection.execute(
        """CREATE TABLE IF NOT EXISTS notifs(
        message TEXT NOT NULL,
        description TEXT NOT NULL,
        read BOOL NOT NULL,
        type TEXT NOT NULL,
        user INT NOT NULL
    );
    """
    )

    # Report Data
    connection.execute(
        """CREATE TABLE IF NOT EXISTS reports(
        message TEXT NOT NULL,
        reporter INT NOT NULL,
        project INT NOT NULL
    );
    """
    )

    # Comment data
    connection.execute(
        """CREATE TABLE IF NOT EXISTS comments(
        thread_id INT,
        message TEXT NOT NULL,
        author INT NOT NULL,
        sent INT NOT NULL,
        parent_id INT
    );
    """
    )

    # Follow data
    connection.execute(
        """CREATE TABLE IF NOT EXISTS follows(
        follower INT,
        followed INT
    );
    """
    )

    # save and exit
    connection.commit()
    connection.close()


if __name__ == "__main__":
    reset("no-drop")

    conn = sqlite3.connect(config.DATA + "data.db")

    conn.execute(
        """INSERT INTO users (username, token, role, bio, github_id, profile_icon) VALUES ("HoodieRocks", "LOREMIPSUM", "admin", "rock", 123897432978, "example.com")"""
    )

    # conn.execute(
    #     'update users set badges = \'{"badges": ["contributor"]}\' WHERE rowid = 1'
    # )

    print(conn.execute("""SELECT * FROM users WHERE rowid = 1""").fetchone())

    conn.commit()
    conn.close()
