from .server import app

_headers = {"Authorization": "Bearer dev-token"}


def test_clear_all_episodes():
    with app.test_client() as test_client:
        response = test_client.delete("/opengluck/episode", headers=_headers)
        assert response.status_code == 204


def test_get_episode():
    with app.test_client() as test_client:
        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "unknown"


def test_insert_episode_1():
    with app.test_client() as test_client:
        # insert an episode
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "episodes": [
                    {"episode": "normal", "timestamp": "2023-04-22T14:00:00+02:00"}
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["episodes"]["nb_inserted"] == 1
        assert response.json["episodes"]["nb_replaced"] == 0
        assert response.json["episodes"]["nb_duplicates"] == 0

        # check that the correct episode is now returned
        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "normal"

        # check that we have a current episode, with timestamp
        response = test_client.get("/opengluck/episode/current", headers=_headers)
        assert response.status_code == 200
        assert response.json == {
            "episode": "normal",
            "timestamp": "2023-04-22T14:00:00+02:00",
        }

        # try to insert the same episode again, this time it should be detected
        # as a duplicate
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "episodes": [
                    {"episode": "normal", "timestamp": "2023-04-22T14:00:00+02:00"}
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["episodes"]["nb_inserted"] == 0
        assert response.json["episodes"]["nb_replaced"] == 0
        assert response.json["episodes"]["nb_duplicates"] == 1

        # check that the webhook was called
        response = test_client.get(
            "/opengluck/webhooks/episode:changed/last?last_n=1",
            headers=_headers,
        )
        assert response.status_code == 200
        assert response.json
        assert len(response.json) == 1
        assert response.json[0]["data"] == {
            "previous": None,
            "new": {
                "timestamp": "2023-04-22T14:00:00+02:00",
                "episode": "normal",
            },
            "cgm-properties": {"has-real-time": True},
        }


def test_insert_episode_2():
    with app.test_client() as test_client:
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "episodes": [
                    {"episode": "high", "timestamp": "2023-04-22T15:00:00+02:00"}
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["episodes"]["nb_inserted"] == 1
        assert response.json["episodes"]["nb_replaced"] == 0
        assert response.json["episodes"]["nb_duplicates"] == 0

        # check that we now have two episodes
        response = test_client.get("/opengluck/episode/last", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T15:00:00+02:00", "episode": "high"},
            {"timestamp": "2023-04-22T14:00:00+02:00", "episode": "normal"},
        ]

        # check that the correct episode is now returned
        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "high"

        # check that the webhook was called
        response = test_client.get(
            "/opengluck/webhooks/episode:changed/last?last_n=1",
            headers=_headers,
        )
        assert response.status_code == 200
        assert response.json
        assert len(response.json) == 1
        assert response.json[0]["data"] == {
            "previous": {
                "timestamp": "2023-04-22T14:00:00+02:00",
                "episode": "normal",
            },
            "new": {
                "timestamp": "2023-04-22T15:00:00+02:00",
                "episode": "high",
            },
            "cgm-properties": {"has-real-time": True},
        }


def test_insert_episode_3():
    with app.test_client() as test_client:
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "episodes": [
                    {"episode": "normal", "timestamp": "2023-04-22T16:00:00+02:00"}
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["episodes"]["nb_inserted"] == 1
        assert response.json["episodes"]["nb_replaced"] == 0
        assert response.json["episodes"]["nb_duplicates"] == 0

        # check that we now have two episodes
        response = test_client.get("/opengluck/episode/last", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T16:00:00+02:00", "episode": "normal"},
            {"timestamp": "2023-04-22T15:00:00+02:00", "episode": "high"},
            {"timestamp": "2023-04-22T14:00:00+02:00", "episode": "normal"},
        ]

        # check that the correct episode is now returned
        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "normal"

        # check that the webhook was called
        response = test_client.get(
            "/opengluck/webhooks/episode:changed/last?last_n=1",
            headers=_headers,
        )
        assert response.status_code == 200
        assert response.json
        assert len(response.json) == 1
        assert response.json[0]["data"] == {
            "previous": {
                "timestamp": "2023-04-22T15:00:00+02:00",
                "episode": "high",
            },
            "new": {
                "timestamp": "2023-04-22T16:00:00+02:00",
                "episode": "normal",
            },
            "cgm-properties": {"has-real-time": True},
        }


def test_last_episodes():
    with app.test_client() as test_client:
        response = test_client.get("/opengluck/episode/last", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T16:00:00+02:00", "episode": "normal"},
            {"timestamp": "2023-04-22T15:00:00+02:00", "episode": "high"},
            {"timestamp": "2023-04-22T14:00:00+02:00", "episode": "normal"},
        ]

        # check that we can requests some of the last episode, not all
        response = test_client.get("/opengluck/episode/last?last_n=2", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T16:00:00+02:00", "episode": "normal"},
            {"timestamp": "2023-04-22T15:00:00+02:00", "episode": "high"},
        ]

        # check that we can requests some of the last episode, not all
        response = test_client.get(
            "/opengluck/episode/last",
            query_string={"until_date": "2023-04-22T15:42:00+02:00"},
            headers=_headers,
        )
        assert response.status_code == 200
        print(response.json)
        assert response.json == [
            {"timestamp": "2023-04-22T15:00:00+02:00", "episode": "high"},
            {"timestamp": "2023-04-22T14:00:00+02:00", "episode": "normal"},
        ]


def test_detect_duplicates():
    with app.test_client() as test_client:
        response = test_client.get(
            "/opengluck/webhooks/episode:changed/last?last_n=1",
            headers=_headers,
        )
        assert response.status_code == 200
        assert response.json
        last_webhook = response.json[0]

        # check that the correct episode is already returned
        response = test_client.get(
            "/opengluck/episode",
            query_string={"until_date": "2023-04-22T15:42:00+02:00"},
            headers=_headers,
        )
        assert response.status_code == 200
        assert response.text == "high"

        # try to insert a duplicate record
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "episodes": [
                    {"episode": "high", "timestamp": "2023-04-22T15:30:00+02:00"}
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["episodes"]["nb_inserted"] == 0
        assert response.json["episodes"]["nb_replaced"] == 0
        assert response.json["episodes"]["nb_duplicates"] == 1

        # check that we now have two episodes
        response = test_client.get("/opengluck/episode/last", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T16:00:00+02:00", "episode": "normal"},
            {"timestamp": "2023-04-22T15:00:00+02:00", "episode": "high"},
            {"timestamp": "2023-04-22T14:00:00+02:00", "episode": "normal"},
        ]

        # check that the correct episode is now returned
        response = test_client.get(
            "/opengluck/episode",
            query_string={"until_date": "2023-04-22T15:42:00+02:00"},
            headers=_headers,
        )

        assert response.status_code == 200
        assert response.text == "high"

        # check that the webhook was NOT called
        response = test_client.get(
            "/opengluck/webhooks/episode:changed/last?last_n=1",
            headers=_headers,
        )
        assert response.status_code == 200
        assert response.json
        assert len(response.json) == 1
        assert response.json[0] == last_webhook
