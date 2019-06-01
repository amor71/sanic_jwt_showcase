import pytest
from sanic import Sanic
import random
import json
from jogging.main import config_app
from jogging import config
from jogging.Models.user import User

username = None
access_token = None
refresh_token = None


@pytest.yield_fixture
def app():
    config.app = Sanic("test_sanic_app")
    config_app()
    yield config.app


@pytest.fixture
def test_cli(loop, app, sanic_client):

    global username
    while username is None:
        i = random.randint(1, 10000)
        username = f"amichay.oren+{i}"
        if User.username_exists(username):
            username = None

    return loop.run_until_complete(sanic_client(app))


async def test_positive_register_(test_cli):
    data = {
        "username": username,
        "password": "testing123G",
        "name": "Amichay Oren",
        "email": f"{username}@gmail.com",
    }
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 201


async def test_positive_login(test_cli):
    data = {"username": username, "password": "testing123G"}
    resp = await test_cli.post("/auth", data=json.dumps(data))
    resp_json = await resp.json()
    print(resp_json)
    global access_token
    access_token = resp_json["access_token"]
    global refresh_token
    refresh_token = resp_json["refresh_token"]
    assert access_token is not None
    assert refresh_token is not None
    assert resp.status == 200


async def test_negative_get_users_by_user(test_cli):
    global access_token
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/users", headers=headers)

    assert resp.status == 403


async def test_positive_get_users_by_manager(test_cli):
    # check who i am
    global access_token
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200
    my_user_id = resp_json["me"]["user_id"]

    # promote to manager
    data = {"scopes": ["user", "manager"]}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{my_user_id}/scopes", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 200

    # re-login to get access token w/ new scope
    data = {"username": username, "password": "testing123G"}
    resp = await test_cli.post("/auth", data=json.dumps(data))
    resp_json = await resp.json()
    print(resp_json)
    access_token = resp_json["access_token"]
    refresh_token = resp_json["refresh_token"]
    assert access_token is not None
    assert refresh_token is not None
    assert resp.status == 200

    # get users
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/users", headers=headers)
    resp_json = await resp.json()

    for row in resp_json:
        user = User(
            user_id=row["user_id"],
            username=row["username"],
            hashed_password=row["hashed_password"],
            scopes=row["scopes"],
            email=row["email"],
            name=row["name"],
        )
        assert False == ("manager" in user.scopes or "admin" in user.scopes)

    assert resp.status == 200


async def test_positive_get_users_by_admin(test_cli):
    # check who i am
    global access_token
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200
    my_user_id = resp_json["me"]["user_id"]

    # promote to manager
    data = {"scopes": ["user", "admin"]}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{my_user_id}/scopes", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 200

    # re-login to get access token w/ new scope
    data = {"username": username, "password": "testing123G"}
    resp = await test_cli.post("/auth", data=json.dumps(data))
    resp_json = await resp.json()
    print(resp_json)
    access_token = resp_json["access_token"]
    refresh_token = resp_json["refresh_token"]
    assert access_token is not None
    assert refresh_token is not None
    assert resp.status == 200

    # get users
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/users?count=1000", headers=headers)
    resp_json = await resp.json()

    users = []
    for row in resp_json:
        users.append(
            User(
                user_id=row["user_id"],
                username=row["username"],
                hashed_password=row["hashed_password"],
                scopes=row["scopes"],
                email=row["email"],
                name=row["name"],
            )
        )
    assert any(["admin" in x.scopes or "manger" in x.scopes for x in users])
    assert resp.status == 200


async def test_positive_paging(test_cli):
    global access_token

    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/users?count=2", headers=headers)
    resp_json = await resp.json()

    assert len(resp_json) == 2
    second_user_id = resp_json[1]["user_id"]

    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/users?count=1&page=1", headers=headers)
    resp_json = await resp.json()
    assert len(resp_json) == 1
    assert second_user_id == resp_json[0]["user_id"]
    assert resp.status == 200
