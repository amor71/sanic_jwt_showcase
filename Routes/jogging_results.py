import datetime
import json
from sanic import response
from sanic.exceptions import (
    SanicException,
    InvalidUsage,
    add_status_code,
    Forbidden,
)
from sanic_jwt.decorators import protected
from jogging.Contectors.darksky import get_weather_condition
from jogging.Routes.auth import retrieve_user
from jogging.Models.jogging_result import JoggingResult, jogging_weekly_report


@add_status_code(409)
class Conflict(SanicException):
    pass


@protected()
async def add_jogging_result(request, *args, **kwargs):
    if (
        request.json is None
        or "date" not in request.json
        or "distance" not in request.json
        or "time" not in request.json
        or "location" not in request.json
    ):
        raise InvalidUsage(
            "invalid payload (should be {date, distance, time, location})"
        )

    distance = int(request.json["distance"])
    if distance <= 0:
        raise InvalidUsage("distance needs to be positive")

    try:
        date = datetime.datetime.strptime(
            request.json["date"], "%Y-%m-%d"
        ).date()
    except ValueError:
        raise InvalidUsage("invalid date (should be 'YYYY-MM-DD')")

    lat_long = request.json["location"].split(" ")

    if len(lat_long) != 2:
        raise InvalidUsage("invalid location (should be 'LAT LONG')")

    try:
        lat = float(lat_long[0])
        long = float(lat_long[1])
    except ValueError:
        raise InvalidUsage(
            "invalid location (lat & long should be floating-point)"
        )

    if not (-90.0 <= lat <= 90.0 and -180 <= long <= 180):
        raise InvalidUsage(
            "invalid location (The latitude must be a number between -90 and 90 and the longitude between -180 and 180)"
        )

    try:
        time = int(request.json["time"])
    except ValueError:
        raise InvalidUsage("invalid time (time should be an integer)")

    if time <= 0:
        raise InvalidUsage("invalid time (time should be positive)")

    condition = await get_weather_condition(lat, long, date)

    if condition is None:
        raise InvalidUsage(
            "can't fetch running conditions for that location & time"
        )

    user_id = retrieve_user(request, args, kwargs).user_id

    jog = JoggingResult(
        user_id,
        request.json["location"],
        date,
        distance,
        time,
        json.dumps(condition["data"][0]),
    )
    id = jog.save()
    return response.json({"result_id": id}, status=201)


@protected()
async def update_jogging_result(request, *args, **kwargs):
    try:
        jogging_id = int(request.path.split("/")[2])
    except ValueError as e:
        raise InvalidUsage(e)

    if jogging_id < 0:
        raise InvalidUsage("invalid id")

    jog = JoggingResult.load_by_jogging_id(jogging_id)

    if jog is None:
        raise InvalidUsage("invalid id")

    user_id_from_token = retrieve_user(request, args, kwargs).user_id
    if user_id_from_token != jog.user_id:
        raise Forbidden("user can only access user jogs")

    if "distance" in request.json:
        distance = request.json["distance"]
        if distance <= 0:
            raise InvalidUsage("distance needs to be positive")
        jog.distance = int(distance)

    if "date" in request.json:
        try:
            date = datetime.datetime.strptime(
                request.json["date"], "%Y-%m-%d"
            ).date()
        except ValueError:
            raise InvalidUsage("invalid date (should be 'YYYY-MM-DD')")

        jog.date = date

    if "location" in request.json:
        location = request.json["location"]
        lat_long = location.split(" ")
        if len(lat_long) != 2:
            raise InvalidUsage("invalid location (should be 'LAT LONG')")
        try:
            lat = float(lat_long[0])
            long = float(lat_long[1])
        except ValueError:
            raise InvalidUsage(
                "invalid location (lat & long should be floating-point)"
            )

        if not (-90.0 <= lat <= 90.0 and -180 <= long <= 180):
            raise InvalidUsage(
                "invalid location (The latitude must be a number between -90"
                " and 90 and the longitude between -180 and 180)"
            )

        jog.location = location

    location = jog.location
    lat_long = location.split(" ")
    lat = float(lat_long[0])
    long = float(lat_long[1])

    condition = await get_weather_condition(lat, long, jog.date)
    if condition is None:
        raise InvalidUsage(
            "can't fetch running conditions for that location & time"
        )
    jog.condition = condition

    if "time" in request.json:
        try:
            time = int(request.json["time"])
        except ValueError:
            raise InvalidUsage("invalid time (time should be an integer)")

        if time <= 0:
            raise InvalidUsage("invalid time (time should be positive)")

        jog.time = time

    jog.save()
    return response.HTTPResponse(status=200)


@protected()
async def get_jogging_results(request, *args, **kwargs):
    page = int(request.args["page"][0]) if "page" in request.args else 0
    limit = int(request.args["count"][0]) if "count" in request.args else 10

    if page < 0 or limit <= 0:
        raise InvalidUsage("invalid paging (page >= 0 and count > 0)")

    q_filter = request.args["filter"][0] if "filter" in request.args else None
    user_id = retrieve_user(request, args, kwargs).user_id

    try:
        rc = JoggingResult.load_by_user_id(user_id, q_filter, page, limit)
    except Exception as e:
        raise InvalidUsage(e)

    return response.json(rc, status=200)


@protected()
async def get_jogging_result(request, *args, **kwargs):
    try:
        jogging_id = int(request.path.split("/")[2])
    except ValueError as e:
        raise InvalidUsage(e)

    if jogging_id < 0:
        raise InvalidUsage("invalid id")

    jog = JoggingResult.load_by_jogging_id(jogging_id)

    if jog is None:
        raise InvalidUsage("invalid id")

    user_id_from_token = retrieve_user(request, args, kwargs).user_id
    if user_id_from_token != jog.user_id:
        raise Forbidden("user can only access user jogs")

    return response.json(jog.__dict__(), status=200)


@protected()
async def get_jogging_weekly_report(request, *args, **kwargs):
    page = int(request.args["page"][0]) if "page" in request.args else 0
    limit = int(request.args["count"][0]) if "count" in request.args else 10

    if page < 0 or limit <= 0:
        raise InvalidUsage("invalid paging (page >= 0 and count > 0)")

    user_id = retrieve_user(request, args, kwargs).user_id
    rc = jogging_weekly_report(user_id, page, limit)
    return response.json(rc, status=200)
