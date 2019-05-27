from sqlalchemy import create_engine
from sqlalchemy.pool import SingletonThreadPool

engine = None


def do_engine():
    global engine
    engine = create_engine(
        "sqlite:///database.db", poolclass=SingletonThreadPool
    )
