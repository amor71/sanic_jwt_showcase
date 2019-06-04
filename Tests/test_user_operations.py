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


async def test_positive_update_name(test_cli):
    global access_token
    # check who i am
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200

    # update me
    my_user_id = resp_json["me"]["user_id"]
    data = {"name": "my new name!"}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{my_user_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204

    # confirm updated!
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200
    assert resp_json["me"]["name"] == data["name"]


async def test_positive_update_email(test_cli):
    global access_token
    # check who i am
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200

    # update me
    my_user_id = resp_json["me"]["user_id"]
    data = {"email": "somebs@a.com"}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{my_user_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204

    # confirm updated!
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200
    assert resp_json["me"]["email"] == data["email"]


async def test_positive_update_password(test_cli):
    global access_token
    # check who i am
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200

    # update me
    my_user_id = resp_json["me"]["user_id"]
    password = "mynewGreatPassword12"
    data = {"password": password}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{my_user_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204

    data = {"username": username, "password": password}
    resp = await test_cli.post("/auth", data=json.dumps(data))
    resp_json = await resp.json()
    print(resp_json)
    access_token = resp_json["access_token"]
    global refresh_token
    refresh_token = resp_json["refresh_token"]
    assert access_token is not None
    assert refresh_token is not None
    assert resp.status == 200


async def test_negative_update_bad_password(test_cli):
    global access_token
    # check who i am
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200

    # update me
    my_user_id = resp_json["me"]["user_id"]
    password = "12"
    data = {"password": password}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{my_user_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 400


async def test_positive_update_email_by_manager(test_cli):
    global access_token
    # check who i am
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200

    # update me
    my_user_id = resp_json["me"]["user_id"]
    data = {"scopes": ["user", "manager"]}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{my_user_id}/scopes", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204
    manager_access_token = access_token

    global username
    username = None
    while username is None:
        i = random.randint(1, 10000)
        username = f"amichay.oren+{i}"
        if User.username_exists(username):
            username = None

    data = {
        "username": username,
        "password": "testing123G",
        "name": "Amichay Oren",
        "email": f"{username}@gmail.com",
    }
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 201

    data = {"username": username, "password": "testing123G"}
    resp = await test_cli.post("/auth", data=json.dumps(data))
    resp_json = await resp.json()
    print(resp_json)
    access_token = resp_json["access_token"]
    refresh_token = resp_json["refresh_token"]
    assert access_token is not None
    assert refresh_token is not None
    assert resp.status == 200

    # check who i am
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200

    new_user_id = resp_json["me"]["user_id"]

    # update other
    my_user_id = resp_json["me"]["user_id"]
    new_name = "some new name"
    data = {"name": new_name}
    headers = {"Authorization": f"Bearer {manager_access_token}"}
    resp = await test_cli.patch(
        f"/users/{new_user_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204

    # confirm updated!
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200
    assert resp_json["me"]["name"] == new_name


async def test_negative_manager_update_manager(test_cli):
    global access_token
    # check who i am
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200

    # update me
    my_user_id = resp_json["me"]["user_id"]
    data = {"scopes": ["user", "manager"]}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{my_user_id}/scopes", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204
    manager_access_token = access_token

    # register second
    global username
    username = None
    while username is None:
        i = random.randint(1, 10000)
        username = f"amichay.oren+{i}"
        if User.username_exists(username):
            username = None

    data = {
        "username": username,
        "password": "testing123G",
        "name": "Amichay Oren",
        "email": f"{username}@gmail.com",
    }
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 201

    # login second
    data = {"username": username, "password": "testing123G"}
    resp = await test_cli.post("/auth", data=json.dumps(data))
    resp_json = await resp.json()
    print(resp_json)
    access_token = resp_json["access_token"]
    refresh_token = resp_json["refresh_token"]
    assert access_token is not None
    assert refresh_token is not None
    assert resp.status == 200

    # check who is second
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200
    new_manager_user_id = resp_json["me"]["user_id"]

    # make second manager
    data = {"scopes": ["user", "manager"]}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{new_manager_user_id}/scopes",
        headers=headers,
        data=json.dumps(data),
    )
    assert resp.status == 204

    # first manager update second manager
    new_name = "some new name"
    data = {"name": new_name}
    headers = {"Authorization": f"Bearer {manager_access_token}"}
    resp = await test_cli.patch(
        f"/users/{new_manager_user_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 403


async def test_positive_admin_update_manager(test_cli):
    global access_token
    # check who i am
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200

    # update me
    my_user_id = resp_json["me"]["user_id"]
    data = {"scopes": ["user", "manager", "admin"]}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{my_user_id}/scopes", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204
    manager_access_token = access_token

    # register second
    global username
    username = None
    while username is None:
        i = random.randint(1, 10000)
        username = f"amichay.oren+{i}"
        if User.username_exists(username):
            username = None

    data = {
        "username": username,
        "password": "testing123G",
        "name": "Amichay Oren",
        "email": f"{username}@gmail.com",
    }
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 201

    # login second
    data = {"username": username, "password": "testing123G"}
    resp = await test_cli.post("/auth", data=json.dumps(data))
    resp_json = await resp.json()
    print(resp_json)
    access_token = resp_json["access_token"]
    refresh_token = resp_json["refresh_token"]
    assert access_token is not None
    assert refresh_token is not None
    assert resp.status == 200

    # check who is second
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200
    new_manager_user_id = resp_json["me"]["user_id"]

    # make second manager
    data = {"scopes": ["user", "manager"]}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{new_manager_user_id}/scopes",
        headers=headers,
        data=json.dumps(data),
    )
    assert resp.status == 204

    # first manager update second manager
    new_name = "some new name"
    data = {"name": new_name}
    headers = {"Authorization": f"Bearer {manager_access_token}"}
    resp = await test_cli.patch(
        f"/users/{new_manager_user_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204


async def test_positive_admin_update_admin(test_cli):
    global access_token
    # check who i am
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200

    # update me
    my_user_id = resp_json["me"]["user_id"]
    data = {"scopes": ["user", "manager", "admin"]}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{my_user_id}/scopes", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204
    manager_access_token = access_token

    # register second
    global username
    username = None
    while username is None:
        i = random.randint(1, 10000)
        username = f"amichay.oren+{i}"
        if User.username_exists(username):
            username = None

    data = {
        "username": username,
        "password": "testing123G",
        "name": "Amichay Oren",
        "email": f"{username}@gmail.com",
    }
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 201

    # login second
    data = {"username": username, "password": "testing123G"}
    resp = await test_cli.post("/auth", data=json.dumps(data))
    resp_json = await resp.json()
    print(resp_json)
    access_token = resp_json["access_token"]
    refresh_token = resp_json["refresh_token"]
    assert access_token is not None
    assert refresh_token is not None
    assert resp.status == 200

    # check who is second
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200
    new_manager_user_id = resp_json["me"]["user_id"]

    # make second manager
    data = {"scopes": ["user", "admin"]}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{new_manager_user_id}/scopes",
        headers=headers,
        data=json.dumps(data),
    )
    assert resp.status == 204

    # first admin update second admin
    new_name = "some new name"
    data = {"name": new_name}
    headers = {"Authorization": f"Bearer {manager_access_token}"}
    resp = await test_cli.patch(
        f"/users/{new_manager_user_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204


async def test_positive_admin_update_user(test_cli):
    global access_token
    # check who i am
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200

    # update me
    my_user_id = resp_json["me"]["user_id"]
    data = {"scopes": ["user", "manager", "admin"]}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.patch(
        f"/users/{my_user_id}/scopes", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204
    manager_access_token = access_token

    # register second
    global username
    username = None
    while username is None:
        i = random.randint(1, 10000)
        username = f"amichay.oren+{i}"
        if User.username_exists(username):
            username = None

    data = {
        "username": username,
        "password": "testing123G",
        "name": "Amichay Oren",
        "email": f"{username}@gmail.com",
    }
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 201

    # login second
    data = {"username": username, "password": "testing123G"}
    resp = await test_cli.post("/auth", data=json.dumps(data))
    resp_json = await resp.json()
    print(resp_json)
    access_token = resp_json["access_token"]
    refresh_token = resp_json["refresh_token"]
    assert access_token is not None
    assert refresh_token is not None
    assert resp.status == 200

    # check who is second
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await test_cli.get("/auth/me", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200
    new_manager_user_id = resp_json["me"]["user_id"]

    # first admin update second user
    new_name = "some new name"
    data = {"name": new_name}
    headers = {"Authorization": f"Bearer {manager_access_token}"}
    resp = await test_cli.patch(
        f"/users/{new_manager_user_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 204
