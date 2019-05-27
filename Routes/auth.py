import bcrypt
from sanic_jwt import exceptions
import config
from Models.user import User


async def authenticate(request, *args, **kwargs):
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if not username or not password:
        raise exceptions.AuthenticationFailed(
            "Missing username or password."
        )

    user = User.get_by_username(username)
    if user is None:
        raise exceptions.AuthenticationFailed("User not found.")

    if not bcrypt.checkpw(
        password.encode("utf-8"), user.hashed_password
    ):
        raise exceptions.AuthenticationFailed("Password is incorrect.")

    return user


def password_validator(password):
    return (
        False
        if not any(char.isdigit() for char in password)
        or not any(char.islower() for char in password)
        or not any(char.isupper() for char in password)
        else True
    )


def encrypt(password):
    return bcrypt.hashpw(password, bcrypt.gensalt(14))


async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
    await config.redis_client.set(
        f"user_id{user_id}", refresh_token
    )  # no TTL for this basic implementation
    assert await config.redis_client.exists(f"user_id{user_id}") is True


async def delete_refresh_token(user_id, refresh_token, *args, **kwargs):
    key = f"user_id{user_id}"
    if await config.redis_client.exists(key):
        token = await config.redis_client.get(key)
        if token == refresh_token.encode("utf-8"):
            await config.redis_client.delete(key)


async def retrieve_refresh_token(request, user_id, *args, **kwargs):
    found_token = await config.redis_client.get(f"user_id{user_id}")
    return found_token
