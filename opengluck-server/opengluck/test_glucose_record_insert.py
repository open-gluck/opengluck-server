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
        response = test_client.delete("/opengluck/instant-glucose", headers=_headers)
        assert response.status_code == 204
        response = test_client.delete("/opengluck/episode", headers=_headers)
        assert response.status_code == 204


def test_get_episode():
    with app.test_client() as test_client:
        response = test_client.get("/opengluck/glucose/current", headers=_headers)
        assert response.status_code == 200
        json = response.json
        assert json
        del json["revision"]
        assert json == {
            "current": None,
            "last_historic": None,
            "current_episode": None,
            "current_episode_timestamp": None,
            "has_cgm_real_time_data": True,
        }


def test_insert_glucose_record_1():
    test_clear_all_glucose_records()
    with app.test_client() as test_client:
        response = test_client.get(
            "/opengluck/webhooks/episode:changed/last", headers=_headers
        )
        assert response.status_code == 200
        assert response.json == []
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

        response = test_client.get("/opengluck/instant-glucose/last", headers=_headers)
        assert response.status_code == 200
        assert response.json
        assert response.json == [
            {
                "mgDl": 123,
                "timestamp": "2023-04-22T14:00:00+02:00",
                "model_name": "Unknown",
                "device_id": "00000000-0000-0000-0000-000000000000",
            }
        ]

        response = test_client.get(
            "/opengluck/webhooks/episode:changed/last", headers=_headers
        )
        assert response.status_code == 200
        assert response.json
        assert [x["data"] for x in response.json] == [
            {
                "previous": None,
                "new": {
                    "timestamp": "2023-04-22T14:00:00+02:00",
                    "episode": "normal",
                },
                "cgm-properties": {"has-real-time": True},
            },
        ]

        response = test_client.get("/opengluck/glucose/current", headers=_headers)
        assert response.status_code == 200
        json = response.json
        assert json
        del json["revision"]
        assert json == {
            "current": {
                "timestamp": "2023-04-22T14:00:00+02:00",
                "mgDl": 123,
                "record_type": "scan",
            },
            "last_historic": None,
            "current_episode": "normal",
            "current_episode_timestamp": "2023-04-22T14:00:00+02:00",
            "has_cgm_real_time_data": True,
        }

        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "normal"


def test_insert_glucose_record_2():
    with app.test_client() as test_client:

        response = test_client.get(
            "/opengluck/webhooks/episode:changed/last", headers=_headers
        )
        assert response.status_code == 200
        assert response.json
        initial_episode_changed = response.json[0]["data"]
        assert response.json[0]["data"] == {
            "previous": None,
            "new": {
                "timestamp": "2023-04-22T14:00:00+02:00",
                "episode": "normal",
            },
            "cgm-properties": {"has-real-time": True},
        }

        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "normal"

        # insert an episode
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "glucose-records": [
                    {
                        "mgDl": 210,
                        "type": "scan",
                        "timestamp": "2023-04-22T15:00:00+02:00",
                    }
                ],
                "episodes": [
                    {"episode": "normal", "timestamp": "2023-04-22T16:00:00+02:00"}
                ],
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["glucose-records"]["success"] is True

        response = test_client.get("/opengluck/glucose/current", headers=_headers)
        assert response.status_code == 200
        json = response.json
        assert json
        del json["revision"]
        assert json == {
            "current": {
                "timestamp": "2023-04-22T15:00:00+02:00",
                "mgDl": 210,
                "record_type": "scan",
            },
            "last_historic": None,
            "current_episode": "normal",
            "current_episode_timestamp": "2023-04-22T16:00:00+02:00",
            "has_cgm_real_time_data": True,
        }

        response = test_client.get("/opengluck/episode", headers=_headers)
        assert response.status_code == 200
        assert response.text == "normal"

        response = test_client.get("/opengluck/episode/last", headers=_headers)
        assert response.status_code == 200
        assert response.json == [
            {"timestamp": "2023-04-22T16:00:00+02:00", "episode": "normal"},
            {"timestamp": "2023-04-22T15:00:00+02:00", "episode": "high"},
            {"timestamp": "2023-04-22T14:00:00+02:00", "episode": "normal"},
        ]

        # FIXME do we want to trigger the episode:changed webhook on
        # intermediate episode changes? like we are high, then disconnected
        # from 15m, then briefly normal and then high again when we reconnect.
        # do we want to trigger the webhook on the normal episode?
        response = test_client.get(
            "/opengluck/webhooks/episode:changed/last", headers=_headers
        )
        assert response.status_code == 200
        assert response.json
        assert response.json[0]["data"] == initial_episode_changed


def test_insert_glucose_records_shift_historic():
    with app.test_client() as test_client:
        response = test_client.delete("/opengluck/glucose", headers=_headers)
        assert response.status_code == 204

        response = test_client.delete(
            "/opengluck/webhooks/glucose:changed", headers=_headers
        )
        assert response.status_code == 204
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "glucose-records": [
                    {
                        "mgDl": 150,
                        "type": "historic",
                        "timestamp": "2023-04-22T14:00:00+02:00",
                    },
                    {
                        "mgDl": 154,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:04:00+02:00",
                    },
                    {
                        "mgDl": 155,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:05:00+02:00",
                    },
                    {
                        "mgDl": 156,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:06:00+02:00",
                    },
                    {
                        "mgDl": 157,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:07:00+02:00",
                    },
                    {
                        "mgDl": 158,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:08:00+02:00",
                    },
                    {
                        "mgDl": 159,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:09:00+02:00",
                    },
                    {
                        "mgDl": 160,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:10:00+02:00",
                    },
                    {
                        "mgDl": 161,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:11:00+02:00",
                    },
                    {
                        "mgDl": 162,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:12:00+02:00",
                    },
                    {
                        "mgDl": 163,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:13:00+02:00",
                    },
                    {
                        "mgDl": 164,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:14:00+02:00",
                    },
                    {
                        "mgDl": 165,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:15:00+02:00",
                    },
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["glucose-records"]["success"] is True

        response = test_client.get(
            "/opengluck/webhooks/glucose:changed/last", headers=_headers
        )
        assert response.status_code == 200
        assert response.json
        print([x["data"] for x in response.json])
        assert [x["data"] for x in response.json] == [
            {
                "previous": None,
                "new": {
                    "timestamp": "2023-04-22T14:14:00+02:00",
                    "mgDl": 164,
                    "record_type": "scan",
                },
                "cgm-properties": {"has-real-time": True},
            }
        ]

        # try to reinsert a new historic record, that would shift the scan records and trigger a glucose change on an inverted timeline
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "glucose-records": [
                    {
                        "mgDl": 150,
                        "type": "historic",
                        "timestamp": "2023-04-22T14:01:00+02:00",
                    },
                ]
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["glucose-records"]["success"] is True

        response = test_client.get(
            "/opengluck/webhooks/glucose:changed/last", headers=_headers
        )
        assert response.status_code == 200
        assert response.json
        print([x["data"] for x in response.json])
        assert [x["data"] for x in response.json] == [
            {
                "previous": None,
                "new": {
                    "timestamp": "2023-04-22T14:14:00+02:00",
                    "mgDl": 164,
                    "record_type": "scan",
                },
                "cgm-properties": {"has-real-time": True},
            },
        ]


def test_insert_glucose_record_with_model_name_and_device_id():
    test_clear_all_glucose_records()
    with app.test_client() as test_client:
        # insert a glucose record
        response = test_client.post(
            "/opengluck/upload",
            headers=_headers,
            method="POST",
            json={
                "device": {"model_name": "test device", "device_id": "test id"},
                "glucose-records": [
                    {
                        "mgDl": 123,
                        "type": "scan",
                        "timestamp": "2023-04-22T14:00:00+02:00",
                    }
                ],
            },
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["glucose-records"]["success"] is True

        response = test_client.get("/opengluck/instant-glucose/last", headers=_headers)
        assert response.status_code == 200
        assert response.json
        assert response.json == [
            {
                "mgDl": 123,
                "timestamp": "2023-04-22T14:00:00+02:00",
                "model_name": "test device",
                "device_id": "test id",
            }
        ]
