import utilities.db as db


def reset(table: str):
    connection = db.make_connection()

    if table != "no-drop":
        db.exec_query(connection, "DROP TABLE :table", table=table)

    # SQLite optimizations
    db.exec_query(connection, "PRAGMA synchronous = NORMAL")
    db.exec_query(connection, "PRAGMA mmap_size = 1000000000")

    # ! This operation may not be supported, disable if you run into issues
    db.exec_query(connection, "PRAGMA journal_mode = WAL")

    # Projects Data
    db.exec_query(
        connection,
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
    """,
    )

    # Versions Data
    db.exec_query(
        connection,
        """CREATE TABLE IF NOT EXISTS versions(
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        primary_download TEXT NOT NULL,
        resource_pack_download TEXT,
        minecraft_versions TEXT NOT NULL,
        version_code TEXT NOT NULL,
        project INT NOT NULL
    );
    """,
    )

    # User data
    db.exec_query(
        connection,
        """CREATE TABLE IF NOT EXISTS users (
        username TEXT NOT NULL UNIQUE, 
        token TEXT NOT NULL UNIQUE, 
        role TEXT NOT NULL, 
        bio TEXT, 
        github_id int UNIQUE,
        discord_id int UNIQUE,
        badges TEXT,
        profile_icon TEXT NOT NULL
    )""",
    )

    # Banned User Data
    db.exec_query(
        connection,
        """CREATE TABLE IF NOT EXISTS banned_users (
        id int NOT NULL UNIQUE,
        expires int,
        reason TEXT
    )""",
    )

    # Notification Data
    db.exec_query(
        connection,
        """CREATE TABLE IF NOT EXISTS notifs(
        message TEXT NOT NULL,
        description TEXT NOT NULL,
        read BOOL NOT NULL,
        type TEXT NOT NULL,
        user INT NOT NULL
    );
    """,
    )

    # Report Data
    db.exec_query(
        connection,
        """CREATE TABLE IF NOT EXISTS reports(
        message TEXT NOT NULL,
        reporter INT NOT NULL,
        project INT NOT NULL
    );
    """,
    )

    # Comment data
    db.exec_query(
        connection,
        """CREATE TABLE IF NOT EXISTS comments(
        thread_id INT,
        message TEXT NOT NULL,
        author INT NOT NULL,
        sent INT NOT NULL,
        parent_id INT
    );
    """,
    )

    # Follow data
    db.exec_query(
        connection,
        """CREATE TABLE IF NOT EXISTS follows(
        follower INT,
        followed INT
    );
    """,
    )

    # save and exit
    connection.commit()
    connection.close()


if __name__ == "__main__":
    reset("no-drop")

    conn = db.make_connection()

    db.exec_query(
        conn,
        """INSERT INTO users (username, token, role, bio, github_id, profile_icon) VALUES ("HoodieRocks", "LOREMIPSUM", "admin", "rock", 123897432978, "https://example.com/")""",
    )

    # text(

    print(db.exec_query(conn, """SELECT * FROM users WHERE rowid = 1""").one())

    conn.commit()
    conn.close()
