import json
import pandas as pd
import sqlite3
from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError
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

    def save(self) -> int:
        connection = engine.connect()
        trans = connection.begin()
        try:
            location = str(self.location)
            s = f"INSERT INTO " \
                f"jogging_results(user_id, location, date, running_distance, time, condition, week_number, year)" \
                f" VALUES({self.user_id}, '{location}', '{self.date}', {self.distance}, {self.time}," \
                f" '{self.condition}', {self.date.isocalendar()[1]}, {self.date.isocalendar()[0]})"
            cursor = connection.connection.cursor()
            cursor.execute(s)
            trans.commit()
            id = cursor.lastrowid
        except Exception as e:
            trans.rollback()
            raise e
        connection.close()

        return id

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
                    user_id, row[0], row[1], row[2], row[3], row[4]
                ).__dict__()
                for row in q_result
            ]
            if q_result is not None
            else []
        )
        connection.close()
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
