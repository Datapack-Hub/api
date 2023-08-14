from utilities import util
from sqlalchemy import text


def reset(table: str):
    connection = util.make_connection()

    if table != "no-drop":
        text(f"DROP TABLE {table}")

    # SQLite optimizations
    text("PRAGMA synchronous = NORMAL")
    text("PRAGMA mmap_size = 1000000000")

    # ! This operation may not be supported, disable if you run into issues
    text("PRAGMA journal_mode = WAL")

    # Projects Data
    text(
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
    text(
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
    text(
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
    text(
        """CREATE TABLE IF NOT EXISTS banned_users (
        id int NOT NULL UNIQUE,
        expires int,
        reason TEXT
    )"""
    )

    # Notification Data
    text(
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
    text(
        """CREATE TABLE IF NOT EXISTS reports(
        message TEXT NOT NULL,
        reporter INT NOT NULL,
        project INT NOT NULL
    );
    """
    )

    # Comment data
    text(
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
    text(
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

    conn = util.make_connection()

    text(
        """INSERT INTO users (username, token, role, bio, github_id, profile_icon) VALUES ("HoodieRocks", "LOREMIPSUM", "admin", "rock", 123897432978, "example.com")"""
    )

    # text(
    #     'update users set badges = \'{"badges": ["contributor"]}\' WHERE rowid = 1'
    # )

    print(text("""SELECT * FROM users WHERE rowid = 1""").fetchone())

    conn.commit()
    conn.close()
