import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

from tables import user_table
from commons import UserModel


engine = db.create_engine("sqlite:///data.db", echo=True)


def make_connection() -> db.Connection:
    return engine.connect()


def exec_query(conn: db.Connection, query: str, **params) -> db.CursorResult:
    q = db.text(query)

    if params:
        q = q.bindparams(**params)
    return conn.execute(q)


def make_session():
    return sessionmaker(bind=engine)()


if __name__ == "__main__":
    user_table.create(bind=make_connection(), checkfirst=True)

    # session.execute(db.insert(user_table).values(username="hoodierocks", token="LOREMIPSUM", role="admin", bio="hoodierocks", github_id=1, profile_icon="https://hoodierocks.com"))
    query = db.select(UserModel.username).where(UserModel.username == "hoodierocks")
    session = make_session()

    check = session.execute(query).fetchall()
    
    print(check)

    # for user in check.scalars():
    #     print(user)
