from sqlalchemy import insert, select
from utilities.commons import UserModel
import utilities.db_utils as db


def reset(table: str):
    conn = db.make_connection()

    if table != "no-drop":
        db.exec_query(conn, "DROP TABLE :table", table=table)

    # SQLite optimizations
    db.exec_query(conn, "PRAGMA synchronous = NORMAL")
    db.exec_query(conn, "PRAGMA mmap_size = 1000000000")

    # ! This operation may not be supported, disable if you run into issues
    db.exec_query(conn, "PRAGMA journal_mode = WAL")

    # Projects Data
    db.exec_query(
        conn,
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
        conn,
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
        conn,
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
        conn,
        """CREATE TABLE IF NOT EXISTS banned_users (
        id int NOT NULL UNIQUE,
        expires int,
        reason TEXT
    )""",
    )

    # Notification Data
    db.exec_query(
        conn,
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
        conn,
        """CREATE TABLE IF NOT EXISTS reports(
        message TEXT NOT NULL,
        reporter INT NOT NULL,
        project INT NOT NULL
    );
    """,
    )

    # Comment data
    db.exec_query(
        conn,
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
        conn,
        """CREATE TABLE IF NOT EXISTS follows(
        follower INT,
        followed INT
    );
    """,
    )

    # save and exit
    conn.commit()
    conn.close()


if __name__ == "__main__":
    reset("no-drop")

    sess = db.make_session()
    
    sess.execute(insert(UserModel).values(username="HoodieRocks", token="LOREMIPSUM", role="admin", bio="rock", github_id=123897432978, profile_icon="https://example.com/"))

    # text(

    print(sess.execute(select(UserModel).where(UserModel.rowid == 1)).one())

    sess.commit()
    sess.close()
