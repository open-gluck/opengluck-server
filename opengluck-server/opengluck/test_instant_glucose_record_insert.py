from datetime import datetime, timedelta

from .config import tz
from .server import app

_headers = {"Authorization": "Bearer dev-token"}


def test_clear_all_instant_glucose_records():
    with app.test_client() as test_client:
        response = test_client.delete("/opengluck/instant-glucose", headers=_headers)
        assert response.status_code == 204


def test_insert_glucose_record():
    test_clear_all_instant_glucose_records()
    with app.test_client() as test_client:
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        one_minute_ago_iso = one_minute_ago.astimezone(tz).isoformat()
        response = test_client.post(
            "/opengluck/instant-glucose/upload",
            headers=_headers,
            method="POST",
            json={
                "instant-glucose-records": [
                    {
                        "mgDl": 123,
                        "timestamp": one_minute_ago_iso,
                        "model_name": "test-model",
                        "device_id": "test-device",
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["success"]

        response = test_client.get("/opengluck/instant-glucose/last", headers=_headers)
        assert response.status_code == 200
        assert response.json
        assert response.json == [
            {
                "mgDl": 123,
                "timestamp": one_minute_ago_iso,
                "model_name": "test-model",
                "device_id": "test-device",
            }
        ]

        response = test_client.get("/opengluck/last", headers=_headers)
        assert response.status_code == 200
        assert response.json
        assert "instant-glucose-records" in response.json
        last_instant = response.json["instant-glucose-records"]
        assert last_instant == [
            {
                "mgDl": 123,
                "timestamp": one_minute_ago_iso,
                "model_name": "test-model",
                "device_id": "test-device",
            }
        ]
