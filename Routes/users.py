from sanic import response
from sanic.exceptions import (
    SanicException,
    InvalidUsage,
    add_status_code,
    Forbidden,
)
from sanic_jwt.decorators import scoped, protected
from jogging.Models.user import User
from jogging.Routes.auth import retrieve_user
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
        raise InvalidUsage("invalid payload (should be {username, password})")

    password = request.json["password"]
    if not password_validator(password):
        raise InvalidUsage("password does not match minimum requirements")

    username = request.json["username"]
    if User.username_exists(username):
        raise Conflict(f"username {username} already exists")

    email = request.json["email"] if "email" in request.json else None
    name = request.json["name"] if "name" in request.json else None
    user = User(
        None, username, encrypt(request.json["password"]), ["user"], email, name
    )
    user.save()

    return response.HTTPResponse(status=201)


@scoped(["manager", "admin"], False)
async def get_users(request, *args, **kwargs):
    page = int(request.args["page"][0]) if "page" in request.args else 0
    limit = int(request.args["count"][0]) if "count" in request.args else 10

    if page < 0 or limit <= 0:
        raise InvalidUsage("invalid paging (page >= 0 and count > 0)")

    user_from_token = retrieve_user(request, args, kwargs)
    if user_from_token is None:
        raise InvalidUsage("invalid parameter (maybe expired?)")
    user_id = user_from_token.user_id
    user = User.get_by_user_id(user_id)

    try:
        rc = user.get_users(page, limit)
    except Exception as e:
        raise InvalidUsage(e)

    return response.json(rc, status=200)


@protected()
async def update_user_scope(request, *args, **kwargs):
    if request.json is None:
        raise InvalidUsage("invalid payload (empty payload not allowed)")

    try:
        requested_user_id = int(request.path.split("/")[2])
    except ValueError as e:
        raise InvalidUsage(e)

    user_from_token = retrieve_user(request, args, kwargs)
    if user_from_token is None:
        raise InvalidUsage("invalid parameter (maybe expired?)")

    user = User.get_by_user_id(requested_user_id)
    if user is None:
        raise InvalidUsage("invalid user")

    if "scopes" in request.json:
        print(request.json)
        user.update_scopes(request.json["scopes"])

    user.save(modifying_user_id=user_from_token.user_id)

    return response.HTTPResponse(status=204)


@protected()
async def delete_user(request, *args, **kwargs):
    try:
        requested_user_id = int(request.path.split("/")[2])
    except ValueError as e:
        raise InvalidUsage(e)

    user_from_token = retrieve_user(request, args, kwargs)
    if user_from_token is None:
        raise InvalidUsage("invalid parameter (maybe expired?)")

    user = User.get_by_user_id(requested_user_id)
    if user is None:
        raise InvalidUsage("invalid user")

    if (
        "admin" not in user_from_token.scopes
        and "manager" not in user_from_token.scopes
    ):
        if requested_user_id != user_from_token.user_id:
            raise Forbidden(f"user can only update self")

    user = User.get_by_user_id(requested_user_id)
    if not user:
        raise InvalidUsage("invalid parameter")

    if (
        "manager" in user_from_token.scopes
        and "admin" not in user_from_token.scopes
        and ("manager" in user.scopes or "admin" in user.scopes)
    ):
        if requested_user_id != user_from_token.user_id:
            raise Forbidden(f"manager can only update manager")

    user.expire(user_from_token.user_id)

    return response.HTTPResponse(status=204)


@protected()
async def update_user(request, *args, **kwargs):
    if request.json is None:
        raise InvalidUsage("invalid payload (empty payload not allowed)")
    try:
        requested_user_id = int(request.path.split("/")[2])
    except ValueError as e:
        raise InvalidUsage(e)

    user_from_token = retrieve_user(request, args, kwargs)
    if user_from_token is None:
        raise InvalidUsage("invalid parameter (maybe expired?)")

    if (
        "admin" not in user_from_token.scopes
        and "manager" not in user_from_token.scopes
    ):
        if requested_user_id != user_from_token.user_id:
            raise Forbidden(f"user can only update self")

    user = User.get_by_user_id(requested_user_id)
    if not user:
        raise InvalidUsage("invalid parameter")

    if (
        "manager" in user_from_token.scopes
        and "admin" not in user_from_token.scopes
        and ("manager" in user.scopes or "admin" in user.scopes)
    ):
        if requested_user_id != user_from_token.user_id:
            raise Forbidden(f"manager can only update manager")

    if "password" in request.json:
        password = request.json["password"]
        if not password_validator(password):
            raise InvalidUsage("password does not match minimum requirements")

        user.update_password(encrypt(password))
    if "email" in request.json:
        user.update_email(request.json["email"])
    if "name" in request.json:
        user.update_name(request.json["name"])

    user.save(modifying_user_id=user_from_token.user_id)

    return response.HTTPResponse(status=204)
