from sqlalchemy.sql import text
from .dbhelper import engine


class User(object):
    def __init__(
        self,
        user_id,
        username,
        hashed_password,
        roll_id=1,
        *args,
        **kwargs
    ):
        self.user_id = user_id
        self.username = username
        self.hashed_password = hashed_password
        self.roll_id = roll_id

    def to_dict(self):
        return {"user_id": self.user_id, "username": self.username}

    def save(self):
        connection = engine.connect()
        trans = connection.begin()
        try:
            s = text(
                "INSERT INTO users(username, hashed_password, roll_id) "
                "VALUES(:username, :hashed_password, :roll_id)"
            )
            connection.execute(
                s,
                username=self.username,
                hashed_password=self.hashed_password,
                roll_id=self.roll_id,
            )
            trans.commit()
        except:
            trans.rollback()
            raise
        connection.close()

    @classmethod
    def get_by_username(cls, username):
        assert engine
        s = text(
            "SELECT user_id, username, hashed_password, roll_id "
            "FROM users "
            "WHERE username = :username AND expire_date is null"
        )
        connection = engine.connect()
        rc = connection.execute(s, username=username).fetchone()
        if rc is not None:
            rc = User(rc[0], rc[1], rc[2].decode("utf-8"), rc[3])

        connection.close()
        return rc

    @classmethod
    def username_exists(cls, username):
        assert engine
        s = text(
            "SELECT * "
            "FROM users "
            "WHERE username = :username AND expire_date is null"
        )
        connection = engine.connect()

        rc = (
            False
            if connection.execute(s, username=username).fetchone()
            is None
            else True
        )
        connection.close()
        return rc
