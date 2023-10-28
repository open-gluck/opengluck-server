from .server import app

_headers = {"Authorization": "Bearer dev-token"}


def test_clear_all_instant_glucose_records():
    with app.test_client() as test_client:
        response = test_client.delete("/opengluck/instant-glucose", headers=_headers)
        assert response.status_code == 204


def test_insert_glucose_record():
    test_clear_all_instant_glucose_records()
    with app.test_client() as test_client:
        response = test_client.post(
            "/opengluck/instant-glucose/upload",
            headers=_headers,
            method="POST",
            json={
                "instant-glucose-records": [
                    {
                        "mgDl": 123,
                        "timestamp": "2023-04-22T14:00:00+02:00",
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
                "timestamp": "2023-04-22T14:00:00+02:00",
                "model_name": "test-model",
                "device_id": "test-device",
            }
        ]
