from sqlalchemy.sql import text
from .dbhelper import engine


class JoggingResult(object):
    def __init__(
        self,
        user_id,
        location,
        date,
        distance,
        time,
        condition
    ):
        self.user_id = user_id
        self.location = location
        self.date = date
        self.distance = distance
        self.time = time
        self.condition = condition

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
                condition=self.condition
            )
            trans.commit()
        except:
            trans.rollback()
            raise
        connection.close()


