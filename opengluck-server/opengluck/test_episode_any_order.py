from .server import app

_headers = {"Authorization": "Bearer dev-token"}


def test_insert_whatever_order():
    with app.test_client() as test_client:
        response = test_client.delete("/opengluck/episode", headers=_headers)
        assert response.status_code == 204

        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "unknown"

        # insert two episodes in the ascending order
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "episodes": [
                    {"episode": "normal", "timestamp": "2023-04-22T14:00:00+02:00"},
                    {"episode": "high", "timestamp": "2023-04-22T15:00:00+02:00"},
                ]
            },
        )
        assert response.status_code == 200

        response = test_client.get("/opengluck/episode/last", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T15:00:00+02:00", "episode": "high"},
            {"timestamp": "2023-04-22T14:00:00+02:00", "episode": "normal"},
        ]

        # clear the episodes
        response = test_client.delete("/opengluck/episode", headers=_headers)

        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "unknown"

        # insert two episodes in the ascending order
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "episodes": [
                    {"episode": "high", "timestamp": "2023-04-22T15:00:00+02:00"},
                    {"episode": "normal", "timestamp": "2023-04-22T14:00:00+02:00"},
                ]
            },
        )
        assert response.status_code == 200

        response = test_client.get("/opengluck/episode/last", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T15:00:00+02:00", "episode": "high"},
            {"timestamp": "2023-04-22T14:00:00+02:00", "episode": "normal"},
        ]


def test_insert_episodes_skip_implicit_duplicates():
    with app.test_client() as test_client:
        response = test_client.delete("/opengluck/episode", headers=_headers)
        assert response.status_code == 204

        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "unknown"

        # insert two episodes in the ascending order
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "episodes": [
                    {"episode": "normal", "timestamp": "2023-04-22T14:00:00+02:00"},
                    {"episode": "normal", "timestamp": "2023-04-22T15:00:00+02:00"},
                ]
            },
        )
        assert response.status_code == 200

        response = test_client.get("/opengluck/episode/last", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T14:00:00+02:00", "episode": "normal"},
        ]

        # clear the episodes
        response = test_client.delete("/opengluck/episode", headers=_headers)

        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "unknown"

        # insert two episodes in the ascending order
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "episodes": [
                    {"episode": "normal", "timestamp": "2023-04-22T15:00:00+02:00"},
                    {"episode": "normal", "timestamp": "2023-04-22T14:00:00+02:00"},
                ]
            },
        )
        assert response.status_code == 200

        response = test_client.get("/opengluck/episode/last", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T14:00:00+02:00", "episode": "normal"},
        ]
