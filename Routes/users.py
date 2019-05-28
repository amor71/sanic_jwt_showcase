from sanic import response
from sanic.exceptions import (
    SanicException,
    InvalidUsage,
    add_status_code,
)
from jogging.Models.user import User
from .auth import encrypt, password_validator


@add_status_code(409)
class Conflict(SanicException):
    pass


async def register(request, *args, **kwargs):
    if (
        request.json is None
        or "username" not in request.json
        or "password" not in request.json
    ):
        raise InvalidUsage(
            "invalid payload (should be {username, password})"
        )

    password = request.json["password"]
    if not password_validator(password):
        raise InvalidUsage(
            "password does not match minimum requirements"
        )

    username = request.json["username"]
    if User.username_exists(username):
        raise Conflict(f"username {username} already exists")

    user = User(None, username, encrypt(request.json["password"]))
    user.save()

    return response.HTTPResponse(status=201)
