import sqlite3

import config


def reset(table: str):
    connection = sqlite3.connect(config.DATA + "data.db")

    if table != "no-drop":
        connection.execute(f"DROP TABLE {table}")

    # SQLite optimizations
    connection.execute("PRAGMA synchronous = NORMAL")

    # ! This operation may not be supported on all OSes, disable if you run into issues
    connection.execute("PRAGMA journal_mode = wal")

    # Enable foreign keys
    connection.execute("PRAGMA foreign_keys = ON")

    # Projects Data
    connection.execute(
        """CREATE TABLE IF NOT EXISTS projects(
        type TEXT NOT NULL, 
        author INT NOT NULL, 
        title TEXT NOT NULL, 
        description TEXT NOT NULL,
        body TEXT NOT NULL, 
        icon TEXT, 
        url TEXT NOT NULL UNIQUE, 
        status TEXT NOT NULL DEFAULT "draft", 
        category TEXT NOT NULL,
        uploaded INT NOT NULL,
        updated INT NOT NULL,
        mod_message TEXT,
        downloads INT NOT NULL DEFAULT 0,
        featured_until INT);
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
        """CREATE TABLE comments (
                project_id INTEGER,
                message TEXT NOT NULL,
                author INT NOT NULL,
                left_boundary INT,
                right_boundary INT,
                parent_id INT,
                FOREIGN KEY (parent_id) REFERENCES comments(rowid)
            );"""
    )

    # Trigger to auto add new comment row for every new project
    connection.execute(
        """CREATE TRIGGER insert_other_table_trigger
        AFTER INSERT ON other_table
        BEGIN
            INSERT INTO comments (project_id, message, author, left_boundary, right_boundary, parent_id)
            VALUES (NEW.ID, 'New comment', 123, NULL, NULL, NULL);
        END;"""
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
