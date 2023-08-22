import config

from sqlalchemy import Connection, CursorResult, create_engine, text
from sqlalchemy.orm import sessionmaker

from commons import UserModel


engine = create_engine("sqlite:///data.db")

def make_connection() -> Connection:
    return engine.connect()


def exec_query(conn: Connection, query: str, **params) -> CursorResult:
    q = text(query)

    if params:
        q = q.bindparams(**params)
    return conn.execute(q)

def make_session():
    return sessionmaker(bind=engine)()


if __name__ == "__main__":
    session = make_session()
    user_query = session.query(UserModel).all()
    
    for user in user_query:
        print(user.__dict__)