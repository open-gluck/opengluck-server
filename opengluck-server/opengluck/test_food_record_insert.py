import time
from datetime import datetime

from .config import tz
from .server import app

_headers = {"Authorization": "Bearer dev-token"}


def test_clear_all():
    with app.test_client() as test_client:
        response = test_client.delete("/opengluck/food", headers=_headers)
        assert response.status_code == 204


def test_insert_food_1():
    test_clear_all()
    with app.test_client() as test_client:
        # insert a food

        response = test_client.get("/opengluck/revision", headers=_headers)
        assert response.status_code == 200
        assert response.json
        start_revision = response.json["revision"]

        # create a date one hour ago, in ISO format
        timestamp = datetime.fromtimestamp(time.time() - 3600, tz=tz).isoformat()

        # insert a record
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "food-records": [
                    {
                        "id": "id1",
                        "timestamp": timestamp,
                        "deleted": False,
                        "name": "Food 1",
                        "carbs": 12,
                        "comps": {"glucose_speed": "custom", "comp": 1.42},
                        "record_until": None,
                        "remember_recording": True,
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["food-records"]["success"] is True

        response = test_client.get("/opengluck/last", headers=_headers)
        assert response.status_code == 200
        json = response.json
        assert json
        assert json["food-records"] == [
            {
                "id": "id1",
                "timestamp": timestamp,
                "deleted": False,
                "name": "Food 1",
                "carbs": 12,
                "comps": {"glucose_speed": "custom", "comp": 1.42},
                "record_until": None,
                "remember_recording": True,
            }
        ]
        response = test_client.get("/opengluck/revision", headers=_headers)
        assert response.status_code == 200
        assert response.json
        revision = response.json["revision"]

        # inserting a record should bump the revision
        assert revision > start_revision

        # try to insert the same record again, and assert we have the same revision
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "food-records": [
                    {
                        "id": "id1",
                        "timestamp": timestamp,
                        "deleted": False,
                        "name": "Food 1",
                        "carbs": 12,
                        "comps": {"glucose_speed": "custom", "comp": 1.42},
                        "record_until": None,
                        "remember_recording": True,
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["food-records"]["success"] is True
        response = test_client.get("/opengluck/revision", headers=_headers)
        assert response.status_code == 200
        assert response.json
        assert response.json["revision"] == revision

        # insert a new record with the same timestamp, but a different value
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "food-records": [
                    {
                        "id": "id1",
                        "timestamp": timestamp,
                        "deleted": False,
                        "name": "Food 1",
                        "carbs": 22,
                        "comps": {"glucose_speed": "custom", "comp": 1.42},
                        "record_until": None,
                        "remember_recording": True,
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["food-records"]["success"] is True
        response = test_client.get("/opengluck/revision", headers=_headers)
        assert response.status_code == 200
        assert response.json
        assert response.json["revision"] > revision


def test_replace_food():
    test_clear_all()
    with app.test_client() as test_client:
        # insert a food

        response = test_client.get("/opengluck/revision", headers=_headers)
        assert response.status_code == 200
        assert response.json
        start_revision = response.json["revision"]

        # create a date one hour ago, in ISO format
        timestamp1 = datetime.fromtimestamp(time.time() - 3600, tz=tz).isoformat()
        timestamp2 = datetime.fromtimestamp(time.time() - 3636, tz=tz).isoformat()

        # insert a record
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "food-records": [
                    {
                        "id": "id1",
                        "timestamp": timestamp1,
                        "deleted": False,
                        "name": "Food 1",
                        "carbs": 22,
                        "comps": {"glucose_speed": "custom", "comp": 1.42},
                        "record_until": None,
                        "remember_recording": True,
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["food-records"]["success"] is True

        response = test_client.get("/opengluck/revision", headers=_headers)
        assert response.status_code == 200
        assert response.json
        revision = response.json["revision"]

        # inserting a record should bump the revision
        assert revision > start_revision

        # try to modify the timestamp of the record we inserted, and make sure
        # it has been replaced
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "food-records": [
                    {
                        "id": "id1",
                        "timestamp": timestamp2,
                        "deleted": False,
                        "name": "Food 1",
                        "carbs": 22,
                        "comps": {"glucose_speed": "custom", "comp": 1.42},
                        "record_until": None,
                        "remember_recording": True,
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["food-records"]["success"] is True
        response = test_client.get("/opengluck/revision", headers=_headers)
        assert response.status_code == 200
        assert response.json
        assert response.json["revision"] > revision

        response = test_client.get("/opengluck/last", headers=_headers)
        assert response.status_code == 200
        json = response.json
        assert json
        assert json["food-records"] == [
            {
                "id": "id1",
                "timestamp": timestamp2,
                "deleted": False,
                "name": "Food 1",
                "carbs": 22,
                "comps": {"glucose_speed": "custom", "comp": 1.42},
                "record_until": None,
                "remember_recording": True,
            }
        ]
