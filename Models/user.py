import json
from sqlalchemy.sql import text
from .dbhelper import engine


class User(object):
    def __init__(
        self,
        user_id,
        username,
        hashed_password,
        scopes,
        email,
        name=None,
        exists=False,
    ):
        self.user_id = user_id
        self.username = username
        self.hashed_password = hashed_password
        self.scopes = scopes
        self.email = email
        self.name = name
        self.modified = False
        self.exists = exists

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "name": self.name,
            "email": self.email,
            "scopes": self.scopes,
        }

    def __str__(self):
        return json.dumps(self.to_dict())

    def update_password(self, hashed_password):
        self.hashed_password = hashed_password
        self.modified = True

    def update_email(self, new_email):
        self.email = new_email
        self.modified = True

    def update_name(self, new_name):
        self.name = new_name
        self.modified = True

    def update_scopes(self, new_scopes):
        self.scopes = new_scopes
        self.modified = True

    def _save_new(self):
        connection = engine.connect()
        trans = connection.begin()
        try:
            s = text(
                "INSERT INTO users(username, hashed_password, scopes, name, email) "
                "VALUES(:username, :hashed_password, :scopes, :name, :email)"
            )
            connection.execute(
                s,
                username=self.username,
                hashed_password=self.hashed_password,
                scopes=json.dumps(self.scopes),
                name=self.name,
                email=self.email,
            )
            trans.commit()
        except:
            trans.rollback()
            raise
        connection.close()

    def _save_updates(self, modify_user_id):
        connection = engine.connect()
        trans = connection.begin()
        try:
            s = text(
                "UPDATE users "
                "SET email=:email, name=:name, hashed_password=:hashed_password, scopes=:scopes,"
                "username=:username, modify_user_id=:modify_user_id, modified_at=datetime('now') "
                "WHERE user_id=:user_id"
            )

            try:
                password = self.hashed_password.encode("utf-8")
            except AttributeError:
                password = self.hashed_password

            connection.execute(
                s,
                user_id=self.user_id,
                username=self.username,
                hashed_password=password,
                name=self.name,
                email=self.email,
                scopes=json.dumps(self.scopes),
                modify_user_id=modify_user_id,
            )
            trans.commit()
        except:
            trans.rollback()
            raise
        connection.close()

    def save(self, modifying_user_id=None):
        assert engine

        if not self.exists:
            self._save_new()
        elif self.modified:
            self._save_updates(
                modifying_user_id if modifying_user_id else self.user_id
            )

    def get_users(self, page: int, limit: int) -> list:
        assert engine
        connection = engine.connect()
        rc = []
        try:
            s = "SELECT user_id, username, hashed_password, scopes, email, name FROM users "

            if "admin" not in self.scopes:
                s += " WHERE scopes = :scopes "

            s += " ORDER BY date(create_date) LIMIT :limit OFFSET :page"

            q_result = connection.execute(
                text(s), scopes=json.dumps(["user"]), page=page, limit=limit
            ).fetchall()

            print(s, json.dumps(["user"]))
            if q_result:
                for row in q_result:
                    rc.append(
                        User(
                            row[0],
                            row[1],
                            row[2].decode("utf-8"),
                            json.loads(row[3]),
                            row[4],
                            row[5],
                            True,
                        )
                    )
        except:
            raise

        connection.close()
        return rc

    @classmethod
    def get_by_username(cls, username):
        assert engine
        s = text(
            "SELECT user_id, username, hashed_password, scopes, email, name "
            "FROM users "
            "WHERE username = :username AND expire_date is null"
        )
        connection = engine.connect()
        rc = connection.execute(s, username=username).fetchone()
        if rc is not None:
            rc = User(
                rc[0],
                rc[1],
                rc[2].decode("utf-8"),
                json.loads(rc[3]),
                rc[4],
                rc[5],
                True,
            )

        connection.close()
        return rc

    @classmethod
    def get_by_user_id(cls, user_id):
        assert engine
        s = text(
            "SELECT user_id, username, hashed_password, scopes, email, name "
            "FROM users "
            "WHERE user_id = :user_id"
        )
        connection = engine.connect()
        rc = connection.execute(s, user_id=user_id).fetchone()
        if rc is not None:
            rc = User(
                rc[0],
                rc[1],
                rc[2].decode("utf-8"),
                json.loads(rc[3]),
                rc[4],
                rc[5],
                True,
            )

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
            if connection.execute(s, username=username).fetchone() is None
            else True
        )
        connection.close()
        return rc
