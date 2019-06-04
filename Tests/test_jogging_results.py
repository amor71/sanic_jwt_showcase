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
        username = f"amichay.oren+{i}@gmail.com"
        if User.username_exists(username):
            username = None

    return loop.run_until_complete(sanic_client(app))


async def test_positive_register_(test_cli):
    data = {"username": username, "password": "testing123G"}
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


async def test_negative_jogging_result(test_cli):
    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "date": "1971-06-20",
        "distance": 2000,
        "time": 405,
        "location": "32.0853 34.7818",
    }
    resp = await test_cli.post(
        "/results", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 400


async def test_positive_jogging_result(test_cli):
    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "date": "2015-06-20",
        "distance": 2000,
        "time": 405,
        "location": "32.0853 34.7818",
    }
    resp = await test_cli.post(
        "/results", headers=headers, data=json.dumps(data)
    )
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 201


async def test_positive_load_dataset(test_cli):
    import csv

    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}

    dsreader = csv.reader(open("jogging_dataset.csv"), delimiter=",")
    for row in dsreader:
        data = {
            "date": row[0],
            "location": row[1],
            "distance": int(row[2]),
            "time": int(row[3]),
        }
        resp = await test_cli.post(
            "/results", headers=headers, data=json.dumps(data)
        )
        resp_json = await resp.json()
        print(resp_json)
        assert resp.status == 201


async def test_negative_jogging_result_no_uath(test_cli):
    global access_token
    global refresh_token
    data = {
        "date": "2015-06-20",
        "distance": 2000,
        "time": 405,
        "location": "32.0853 34.7818",
    }
    resp = await test_cli.post("/results", data=json.dumps(data))
    assert resp.status == 400


async def test_positive_get_all_results(test_cli):
    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = await test_cli.get("/results", headers=headers)
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 200


async def test_positive_get_paging(test_cli):
    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = await test_cli.get("/results?page=0&count=2", headers=headers)
    resp_json = await resp.json()
    assert resp.status == 200
    assert len(resp_json) == 2

    resp = await test_cli.get("/results?page=1&count=1", headers=headers)
    resp_json = await resp.json()
    assert resp.status == 200
    assert len(resp_json) == 1


async def test_negative_bad_paging(test_cli):
    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = await test_cli.get("/results?page=-1&count=2", headers=headers)
    assert resp.status == 400

    resp = await test_cli.get("/results?page=1&count=0", headers=headers)
    assert resp.status == 400


async def test_negative_sql_injection(test_cli):
    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = await test_cli.get(
        "/results?page=0&count=2&filter=%3Bdrop table users%3B", headers=headers
    )
    assert resp.status == 400


async def test_positive_check_filters(test_cli):
    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = await test_cli.get(
        "/results?page=0&count=2&filter=date eq '2019-07-15'", headers=headers
    )
    resp_json = await resp.json()
    assert resp.status == 200
    assert len(resp_json) == 1

    resp = await test_cli.get(
        "/results?filter=(date lt '2018-01-01') AND (time lt 500)",
        headers=headers,
    )
    resp_json = await resp.json()
    print (resp_json)
    assert resp.status == 200
    assert len(resp_json) == 9

    resp = await test_cli.get(
        "/results?filter=distance ne 2000", headers=headers
    )
    resp_json = await resp.json()
    assert resp.status == 200
    assert len(resp_json) == 10

    resp = await test_cli.get(
        "/results?filter=distance ne 2000 and ((time lt 400) and (time gt 390))",
        headers=headers,
    )
    resp_json = await resp.json()

    assert resp.status == 200
    assert len(resp_json) == 0


async def test_positive_update_and_get(test_cli):
    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "date": "2015-06-20",
        "distance": 2000,
        "time": 405,
        "location": "32.0853 34.7818",
    }

    resp = await test_cli.post(
        "/results", headers=headers, data=json.dumps(data)
    )
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 201

    # distance
    result_id = resp_json['result_id']
    data = {
        "distance": 2100,
    }
    resp = await test_cli.patch(
        f"/results/{result_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 200
    resp = await test_cli.get(
        f"/results/{result_id}", headers=headers
    )
    resp_json = await resp.json()
    assert resp.status == 200
    assert resp_json['distance'] == data['distance']

    # time
    result_id = resp_json['result_id']
    data = {
        "time": 123,
    }
    resp = await test_cli.patch(
        f"/results/{result_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 200
    resp = await test_cli.get(
        f"/results/{result_id}", headers=headers
    )
    resp_json = await resp.json()
    assert resp.status == 200
    assert resp_json['time'] == data['time']

    # date
    result_id = resp_json['result_id']
    data = {
        "date": '2019-01-01',
    }
    resp = await test_cli.patch(
        f"/results/{result_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 200
    resp = await test_cli.get(
        f"/results/{result_id}", headers=headers
    )
    resp_json = await resp.json()
    assert resp.status == 200
    assert resp_json['date'] == data['date']

    # location
    result_id = resp_json['result_id']
    data = {
        "location": '32.0853 34.7819',
    }
    resp = await test_cli.patch(
        f"/results/{result_id}", headers=headers, data=json.dumps(data)
    )
    assert resp.status == 200
    resp = await test_cli.get(
        f"/results/{result_id}", headers=headers
    )
    resp_json = await resp.json()
    assert resp.status == 200
    assert resp_json['location'] == data['location']


async def test_negative_get(test_cli):
    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = await test_cli.get(
        f"/results/-1", headers=headers)
    assert resp.status == 400

    resp = await test_cli.get(
        f"/results/basdasd", headers=headers)
    assert resp.status == 400


async def test_positive_delete(test_cli):
    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "date": "2015-06-20",
        "distance": 2000,
        "time": 405,
        "location": "32.0853 34.7818",
    }

    resp = await test_cli.post(
        "/results", headers=headers, data=json.dumps(data)
    )
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 201

    # delete
    result_id = resp_json['result_id']
    resp = await test_cli.delete(
        f"/results/{result_id}", headers=headers
    )
    assert resp.status == 204


async def test_negative_delete(test_cli):
    global access_token
    global refresh_token
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "date": "2015-06-20",
        "distance": 2000,
        "time": 405,
        "location": "32.0853 34.7818",
    }

    resp = await test_cli.post(
        "/results", headers=headers, data=json.dumps(data)
    )
    resp_json = await resp.json()
    print(resp_json)
    assert resp.status == 201

    # delete
    result_id = resp_json['result_id']
    resp = await test_cli.delete(
        f"/results/{result_id}", headers=headers
    )
    assert resp.status == 204

    # delete
    result_id = resp_json['result_id']
    resp = await test_cli.delete(
        f"/results/{result_id}", headers=headers
    )
    assert resp.status == 400

    resp = await test_cli.delete(
        f"/results/sadfkjahsdkfhsf", headers=headers
    )
    assert resp.status == 400

    resp = await test_cli.delete(
        f"/results/67676767676767", headers=headers
    )
    assert resp.status == 400



