import sqlalchemy as db

metadata = db.MetaData()


user_table = db.Table(
    "users",
    metadata,
    db.Column("rowid", db.Integer, primary_key=True),
    db.Column("username", db.Text, unique=True, nullable=False),
    db.Column("token", db.Text, unique=True, nullable=False),
    db.Column("role", db.Text, nullable=False),
    db.Column("bio", db.Text),
    db.Column("github_id", db.Integer, unique=True),
    db.Column("discord_id", db.Integer, unique=True),
    db.Column("badges", db.Text),
    db.Column("profile_icon", db.Text, nullable=False),
)
