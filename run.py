import sqlite3
import config

conn = sqlite3.connect(config.db)

print(conn.execute("update users set role = 'admin' where username = 'Silabear'").fetchall())

conn.commit()

conn.close()
