import json
from sqlalchemy.sql import text
from .dbhelper import engine


class JoggingResult(object):
    def __init__(self, user_id, location, date, distance, time, condition):
        self.user_id = user_id
        self.location = location
        self.date = date
        self.distance = distance
        self.time = time
        self.condition = condition

    def __dict__(self):
        return {
            "location": self.location,
            "date": self.date,
            "distance": self.distance,
            "time": self.time,
            "condition": json.loads(self.condition),
        }

    def save(self):
        connection = engine.connect()
        trans = connection.begin()
        try:
            s = text(
                "INSERT INTO jogging_results(user_id, location, date, running_distance, time, condition) "
                "VALUES(:user_id, :location, :date, :running_distance, :time, :condition)"
            )
            connection.execute(
                s,
                user_id=self.user_id,
                location=self.location,
                date=self.date,
                running_distance=self.distance,
                time=self.time,
                condition=self.condition,
            )
            trans.commit()
        except:
            trans.rollback()
            raise
        connection.close()

    @classmethod
    def load(cls, user_id: int, q_filter: str, page: int, limit: int) -> list:
        assert engine
        s = (
            "SELECT location, date, running_distance, time, condition "
            "FROM jogging_results "
            "WHERE user_id = :user_id"
        )

        if q_filter:
            q_filter = (
                q_filter.replace("eq", "=")
                .replace("ne", "!=")
                .replace("gt", ">=")
                .replace("lt", "<=")
                .replace("distance", "running_distance")
            )
            s += f" AND ({q_filter})"

        s += " ORDER BY date(date) LIMIT :limit OFFSET :page"

        connection = engine.connect()
        q_result = connection.execute(
            text(s), user_id=user_id, limit=limit, page=page
        ).fetchall()

        rc = (
            [
                JoggingResult(
                    user_id, row[0], row[1], row[2], row[3], row[4]
                ).__dict__()
                for row in q_result
            ]
            if q_result is not None
            else []
        )
        connection.close()
        return rc
