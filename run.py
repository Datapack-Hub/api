import sqlite3
import config

conn = sqlite3.connect(config.db)

print(conn.execute("select * from users").fetchall())

conn.commit()

conn.close()
