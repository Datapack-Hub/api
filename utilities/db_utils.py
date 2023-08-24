import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

from commons import UserModel, Base


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
    Base.metadata.create_all(bind=engine)
    session = make_session()

    # session.execute(db.insert(UserModel).values(username="hoodierocks", token="LOREMIPSUM", role="admin", bio="hoodierocks", github_id=1, profile_icon="https://hoodierocks.com"))
    query = db.select(UserModel.username, UserModel.token).where(
        UserModel.username == "hoodierocks"
    )

    # session.execute(
    #     db.insert(UserModel).values(
    #         username="hello",
    #         role="default",
    #         bio="A new Datapack Hub user!",
    #         github_id=1234,
    #         token="dflhakdflkahsdfkh",
    #         profile_icon="https://cool.dude/",
    #     )
    # )

    check = session.execute(query).all()

    session.commit()
    session.close()
    print(check[0].token)

    # for user in check.scalars():
    #     print(user)
