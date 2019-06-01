import bcrypt
from sanic_jwt import exceptions, Claim
from jogging import config
from jogging.Models.user import User

#
# Authentication Management
#
async def authenticate(request, *args, **kwargs):
    if request.json is None:
        raise exceptions.AuthenticationFailed("missing payload")

    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if not username or not password:
        raise exceptions.AuthenticationFailed("Missing username or password.")

    user = User.get_by_username(username)
    if user is None:
        raise exceptions.AuthenticationFailed("User not found.")

    if not bcrypt.checkpw(
        password.encode("utf-8"), user.hashed_password.encode("utf-8")
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
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(14))


async def scope_extender(user, *args, **kwargs):
    return user.scopes


#
# Token Management
#
async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
    await config.redis_client.set(
        f"user_id:{user_id}", refresh_token
    )  # no TTL for this basic implementation
    assert await config.redis_client.exists(f"user_id:{user_id}") is True


async def retrieve_refresh_token(request, user_id, *args, **kwargs):
    found_token = await config.redis_client.get(f"user_id:{user_id}")
    return found_token


def retrieve_user(request, *args, **kwargs):
    if "user_id" in kwargs:
        user_id = kwargs.get("user_id")
    else:
        if "payload" in kwargs:
            payload = kwargs.get("payload")
        else:
            payload = request.app.auth.extract_payload(request)
        user_id = payload.get("user_id")

    return User.get_by_user_id(user_id)


#
# Custom Claims
#
class NameClaim(Claim):
    key = "name"

    def setup(self, payload, user):
        return user.name if hasattr(user, "name") else None

    def verify(self, value):
        return True


class EmailClaim(Claim):
    key = "email"

    def setup(self, payload, user):
        return user.email if hasattr(user, "email") else None

    def verify(self, value):
        return True
