import sqlite3
connection = sqlite3.connect('data.db')

connection.execute("drop table if exists projects")
connection.execute("drop table if exists users")

connection.execute("create table projects(id INT NOT NULL UNIQUE, type STRING NOT NULL, author INT NOT NULL, title STRING NOT NULL, description STRING NOT NULL, icon STRING, url STRING NOT NULL UNIQUE);")

connection.execute("insert into projects values (1, 'datapack', 1, 'Realistic Item Drops', 'Drops Realsitc', 'https://cdn.discordapp.com/attachments/723984082853298297/1076083669409730590/IMG_2434.png', 'realistic-item-drops');")

c = connection.execute("select type, author, title, icon, url from projects")

for i in c:
    print(i)
    
# User data
connection.execute("create table IF NOT EXISTS users (username string NOT NULL UNIQUE, token string NOT NULL UNIQUE, role string NOT NULL, bio STRING, github_id int NOT NULL UNIQUE)")

connection.commit()
    
connection.close()