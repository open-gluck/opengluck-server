from .server import app

_headers = {"Authorization": "Bearer dev-token"}


def test_insert_earlier_replaces_episode():
    with app.test_client() as test_client:
        response = test_client.delete("/opengluck/episode", headers=_headers)
        assert response.status_code == 204

        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "unknown"

        # insert one episode starting late
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "episodes": [
                    {"episode": "normal", "timestamp": "2023-04-22T15:00:00+02:00"},
                ]
            },
        )
        assert response.status_code == 200

        response = test_client.get("/opengluck/episode/last", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T15:00:00+02:00", "episode": "normal"},
        ]

        # keep the last webhook
        response = test_client.get(
            "/opengluck/webhooks/episode:changed/last?last_n=1",
            headers=_headers,
        )
        assert response.status_code == 200
        assert response.json

        last_webhook = response.json[0]
        # insert another episode, starting earlier
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "episodes": [
                    {"episode": "normal", "timestamp": "2023-04-22T14:00:00+02:00"},
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["episodes"]["nb_inserted"] == 0
        assert response.json["episodes"]["nb_replaced"] == 1
        assert response.json["episodes"]["nb_duplicates"] == 0

        response = test_client.get("/opengluck/episode/last", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T14:00:00+02:00", "episode": "normal"},
        ]

        # check that the webhook was NOT called
        response = test_client.get(
            "/opengluck/webhooks/episode:changed/last?last_n=1",
            headers=_headers,
        )
        assert response.status_code == 200
        assert response.json
        assert len(response.json) == 1
        assert response.json[0] == last_webhook
