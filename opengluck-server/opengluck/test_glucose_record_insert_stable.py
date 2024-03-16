# This test file checks that, when we upload a glucose record that is stable
# compared to the previous ones, we are still able to succesfully trigger
# glucose:changed webhooks once in a while -- even if the glucose hasn't
# technically changed, this will allow for clients to succesfully re-render
# with the still fresh glucose reading.
from .server import app

_headers = {"Authorization": "Bearer dev-token"}


_glucose_records = [
    {
        "mgDl": 130,
        "type": "historic",
        "timestamp": "2023-04-22T14:00:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:01:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:02:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:03:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:04:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:05:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:06:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:07:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:08:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:09:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:10:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:11:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:12:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:13:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:14:00+02:00",
    },
    {
        "mgDl": 150,
        "type": "historic",
        "timestamp": "2023-04-22T14:15:00+02:00",
    },
]

_expected_changed = [
    {
        "previous": {
            "timestamp": "2023-04-22T14:10:00+02:00",
            "mgDl": 150,
            "record_type": "historic",
        },
        "new": {
            "timestamp": "2023-04-22T14:11:00+02:00",
            "mgDl": 150,
            "record_type": "historic",
        },
        "cgm-properties": {"has-real-time": True},
    },
    {
        "previous": {
            "timestamp": "2023-04-22T14:05:00+02:00",
            "mgDl": 150,
            "record_type": "historic",
        },
        "new": {
            "timestamp": "2023-04-22T14:06:00+02:00",
            "mgDl": 150,
            "record_type": "historic",
        },
        "cgm-properties": {"has-real-time": True},
    },
    {
        "previous": {
            "timestamp": "2023-04-22T14:00:00+02:00",
            "mgDl": 130,
            "record_type": "historic",
        },
        "new": {
            "timestamp": "2023-04-22T14:01:00+02:00",
            "mgDl": 150,
            "record_type": "historic",
        },
        "cgm-properties": {"has-real-time": True},
    },
    {
        "previous": None,
        "new": {
            "timestamp": "2023-04-22T14:00:00+02:00",
            "mgDl": 130,
            "record_type": "historic",
        },
        "cgm-properties": {"has-real-time": True},
    },
]


def test_insert_stable_glucose_records_one_by_one():
    with app.test_client() as test_client:
        response = test_client.delete("/opengluck/glucose", headers=_headers)
        assert response.status_code == 204
        response = test_client.delete(
            "/opengluck/webhooks/glucose:changed", headers=_headers
        )
        assert response.status_code == 204
        response = test_client.delete(
            "/opengluck/userdata/last_just_updated_glucose_at", headers=_headers
        )
        assert response.status_code == 204

        for glucose_record in _glucose_records:
            response = test_client.post(
                "/opengluck/upload",
                headers=_headers,
                method="POST",
                json={"glucose-records": [glucose_record]},
            )
            assert response.status_code == 200
            assert response.json
            assert response.json["glucose-records"]["success"] is True

        response = test_client.get(
            "/opengluck/webhooks/glucose:changed/last", headers=_headers
        )
        assert response.status_code == 200
        assert response.json
        assert [x["data"] for x in response.json]
        assert [x["data"] for x in response.json] == _expected_changed
