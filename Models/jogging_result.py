import json
import datetime
from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError
from .dbhelper import engine


class JoggingResult:
    def __init__(
        self, user_id, location, date, distance, time, condition, result_id=None
    ):
        self.user_id = user_id
        self.location = location
        self.date = date
        self.distance = distance
        self.time = time
        self.condition = condition
        self.result_id = result_id

    def __dict__(self):
        return {
            "result_id": self.result_id,
            "user_id": self.user_id,
            "location": self.location,
            "date": str(self.date),
            "distance": self.distance,
            "time": self.time,
            "condition": self.condition,
        }

    def _save(self) -> int:
        connection = engine.connect()
        trans = connection.begin()
        try:
            location = str(self.location)
            s = (
                f"INSERT INTO "
                f"jogging_results(user_id, location, date, running_distance, time, condition, week_number, year)"
                f" VALUES({self.user_id}, '{location}', '{self.date}', {self.distance}, {self.time},"
                f" '{self.condition}', {self.date.isocalendar()[1]}, {self.date.isocalendar()[0]})"
            )
            cursor = connection.connection.cursor()
            cursor.execute(s)
            trans.commit()
            id = cursor.lastrowid
        except Exception as e:
            trans.rollback()
            raise e
        connection.close()

        return id

    def _update(self) -> int:
        connection = engine.connect()
        trans = connection.begin()
        try:
            s = text(
                f"UPDATE jogging_results SET "
                f"user_id=:user_id, location=:location, date=:date,"
                f"running_distance=:distance, time=:time,"
                f"condition=:condition, week_number=:week_number, year=:year "
                f"WHERE result_id=:result_id"
            )
            connection.execute(
                s,
                user_id=self.user_id,
                location=self.location,
                date=self.date,
                distance=self.distance,
                time=self.time,
                condition=json.dumps(self.condition),
                week_number=self.date.isocalendar()[1],
                year=self.date.isocalendar()[0],
                result_id=self.result_id,
            )
            trans.commit()

        except Exception as e:
            trans.rollback()
            raise e
        connection.close()

        return self.result_id

    def save(self) -> int:
        if not self.result_id:
            return self._save()
        else:
            return self._update()

    @staticmethod
    def load_by_user_id(
        user_id: int, q_filter: str, page: int, limit: int
    ) -> list:
        assert engine
        s = (
            "SELECT location, date, running_distance, time, condition, result_id "
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
                .replace(";", "")
            )
            s += f" AND ({q_filter})"

        s += " ORDER BY date(date) LIMIT :limit OFFSET :page"

        connection = engine.connect()
        try:
            q_result = connection.execute(
                text(s), user_id=user_id, limit=limit, page=page
            ).fetchall()
        except OperationalError as e:
            raise e

        rc = (
            [
                JoggingResult(
                    user_id, row[0], row[1], row[2], row[3], row[4], row[5]
                ).__dict__()
                for row in q_result
            ]
            if q_result is not None
            else []
        )
        connection.close()
        return rc

    @staticmethod
    def load_by_jogging_id(result_id: int) -> "JoggingResult":
        assert engine
        s = (
            "SELECT user_id, location, date, running_distance, time, condition "
            "FROM jogging_results "
            "WHERE result_id = :result_id"
        )

        connection = engine.connect()
        rc = None
        try:
            row = connection.execute(text(s), result_id=result_id).fetchone()

            if row is not None:
                rc = JoggingResult(
                    row[0],
                    row[1],
                    datetime.datetime.strptime(row[2], "%Y-%m-%d").date(),
                    row[3],
                    row[4],
                    json.loads(row[5]),
                    result_id,
                )
        except OperationalError as e:
            raise e

        return rc


def jogging_weekly_report(user_id: int, page: int, limit: int) -> dict:
    assert engine
    s = (
        "SELECT avg(time*1.0/running_distance), sum(running_distance), week_number, year "
        "FROM jogging_results "
        "WHERE user_id = :user_id "
        "GROUP BY year, week_number "
        "ORDER BY date LIMIT :limit OFFSET :page"
        ""
    )
    connection = engine.connect()
    rc = {}
    try:
        q_result = connection.execute(
            text(s), user_id=user_id, limit=limit, page=page
        ).fetchall()

        for row in q_result:
            week = {row[2]: (row[0], row[1])}
            if row[3] not in rc:
                rc[row[3]] = [week]
            else:
                rc[row[3]].append(week)

    except OperationalError as e:
        raise e

    return rc
