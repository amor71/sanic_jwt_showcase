import pytest
from sanic import Sanic
import random
import json
from jogging.main import config_app
from jogging import config
from jogging.Models.user import User

username = None
jwt = None
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
        username = f"amichay.oren+{i}@gmail.com"
        if User.username_exists(username):
            username = None

    return loop.run_until_complete(sanic_client(app))


async def test_positive_register_(test_cli):
    data = {"username": username, "password": "testing123G"}
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 201


async def test_negative_register_no_payload(test_cli):
    resp = await test_cli.post("/users")
    assert resp.status == 400


async def test_negative_register_partial_payload(test_cli):
    data = {"username": username}
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 400


async def test_negative_register_password_missing_minimal_req(test_cli):
    data = {"username": username, "password": "1234"}
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 400


async def test_negative_register_already_exists(test_cli):
    data = {"username": username, "password": "testing123G"}
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 409

async def test_positive_register_w_email_and_name(test_cli):
    global username
    username=None
    while username is None:
        i = random.randint(1, 10000)
        username = f"amichay.oren+{i}@gmail.com"
        if User.username_exists(username):
            username = None

    data = {"username": username, "password": "testing123G", "email": username, "name": "Amichay Oren"}
    resp = await test_cli.post("/users", data=json.dumps(data))

    assert resp.status == 201

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


async def test_positive_register_w_email(test_cli):
    global username
    username=None
    while username is None:
        i = random.randint(1, 10000)
        username = f"amichay.oren+{i}@gmail.com"
        if User.username_exists(username):
            username = None

    data = {"username": username, "password": "testing123G", "email": username}
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 201


async def test_positive_register_w_random_username(test_cli):
    global username
    username=None
    while username is None:
        i = random.randint(1, 10000)
        username = f"{i}"
        if User.username_exists(username):
            username = None

    data = {"username": username, "password": "testing123G", "email": 'amichay@gmail.com'}
    resp = await test_cli.post("/users", data=json.dumps(data))
    assert resp.status == 201

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
