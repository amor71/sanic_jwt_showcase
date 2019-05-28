from sqlalchemy import create_engine
from sqlalchemy.pool import SingletonThreadPool

engine = create_engine(
        "sqlite://///Users/amichayoren/dev/python/jogging/database.db", poolclass=SingletonThreadPool
    )
