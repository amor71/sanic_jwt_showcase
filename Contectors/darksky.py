import datetime
from darksky import forecast
from jogging.config import darksky_api_key


async def get_weather_condition(
    lat: float, long: float, date: datetime.date
):
    location = darksky_api_key, lat, long
    dt = datetime.datetime.combine(date, datetime.datetime.min.time())
    conditions = forecast(*location, time=dt.isoformat())

    try:
        rc = conditions["daily"]
    except KeyError:
        rc = None
    return rc
