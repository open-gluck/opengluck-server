from .server import app

_headers = {"Authorization": "Bearer dev-token"}


def test_clear_all_glucose_records():
    with app.test_client() as test_client:
        response = test_client.delete("/opengluck/glucose", headers=_headers)
        assert response.status_code == 204

        response = test_client.delete(
            "/opengluck/webhooks/episode:changed", headers=_headers
        )
        assert response.status_code == 204
        response = test_client.delete("/opengluck/episode", headers=_headers)
        assert response.status_code == 204


def test_insert_glucose_record_1():
    test_clear_all_glucose_records()
    with app.test_client() as test_client:
        response = test_client.get("/opengluck/revision", headers=_headers)
        assert response.status_code == 200
        assert response.json
        start_revision = response.json["revision"]

        # insert a glucose record
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "glucose-records": [
                    {
                        "mgDl": 123,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:00:00+02:00",
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["glucose-records"]["success"] is True

        response = test_client.get("/opengluck/revision", headers=_headers)
        assert response.status_code == 200
        assert response.json
        revision = response.json["revision"]

        # inserting a record should bump the revision
        assert revision > start_revision

        # try to insert the same number, and assert we have the same revision
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "glucose-records": [
                    {
                        "mgDl": 123,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:00:00+02:00",
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["glucose-records"]["success"] is True

        response = test_client.get("/opengluck/revision", headers=_headers)
        assert response.status_code == 200
        assert response.json
        assert response.json["revision"] == revision

        # try to insert another glucose record at the same time, but with a
        # different value
        # this time, revision should be bumped
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "glucose-records": [
                    {
                        "mgDl": 124,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:00:00+02:00",
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["glucose-records"]["success"] is True

        response = test_client.get("/opengluck/revision", headers=_headers)
        assert response.status_code == 200
        assert response.json
        assert response.json["revision"] > revision
