from opengluck.glucose import GlucoseRecord, GlucoseRecordType

from .hba1c import _calculate_hba1c


def test_calculate_hba1c():
    assert _calculate_hba1c([]) is None

    # Single record: avg=100, cv=0
    glucose_records = [
        GlucoseRecord(
            timestamp="2021-01-01T00:00:00",
            mgDl=100,
            record_type=GlucoseRecordType.historic,
        ),
    ]
    result = _calculate_hba1c(glucose_records)
    assert result is not None
    assert abs(result["hba1c"] - 5.702) < 0.00001
    assert abs(result["avg_mgdl"] - 100) < 0.00001
    assert result["cv"] == 0

    # Two records 20 min apart, avg=100 (90→110 interpolated)
    glucose_records = [
        GlucoseRecord(
            timestamp="2021-01-01T00:00:00",
            mgDl=90,
            record_type=GlucoseRecordType.historic,
        ),
        GlucoseRecord(
            timestamp="2021-01-01T00:20:00",
            mgDl=110,
            record_type=GlucoseRecordType.historic,
        ),
    ]
    result = _calculate_hba1c(glucose_records)
    assert result is not None
    assert abs(result["hba1c"] - 5.702) < 0.5
    assert abs(result["avg_mgdl"] - 100) < 0.5
    assert result["cv"] > 0

    glucose_records = [
        GlucoseRecord(
            timestamp="2021-01-01T00:00:00",
            mgDl=90,
            record_type=GlucoseRecordType.historic,
        ),
        GlucoseRecord(
            timestamp="2021-01-01T00:20:00",
            mgDl=111,
            record_type=GlucoseRecordType.historic,
        ),
    ]
    result = _calculate_hba1c(glucose_records)
    assert result is not None
    assert result["hba1c"] > 5.702

    glucose_records = [
        GlucoseRecord(
            timestamp="2021-01-01T00:00:00",
            mgDl=90,
            record_type=GlucoseRecordType.historic,
        ),
        GlucoseRecord(
            timestamp="2021-01-01T00:20:00",
            mgDl=109,
            record_type=GlucoseRecordType.historic,
        ),
    ]
    result = _calculate_hba1c(glucose_records)
    assert result is not None
    assert result["hba1c"] < 5.702

    glucose_records = [
        GlucoseRecord(
            timestamp="2021-01-01T00:00:00",
            mgDl=90,
            record_type=GlucoseRecordType.historic,
        ),
        GlucoseRecord(
            timestamp="2021-01-01T00:01:00",
            mgDl=95,
            record_type=GlucoseRecordType.historic,
        ),
    ]
    result = _calculate_hba1c(glucose_records)
    assert result is not None
    assert abs(result["hba1c"] - 5.5226) < 0.00001

    # Records with a >60 min gap
    glucose_records = [
        GlucoseRecord(
            timestamp="2021-01-01T00:00:00",
            mgDl=90,
            record_type=GlucoseRecordType.historic,
        ),
        GlucoseRecord(
            timestamp="2021-01-01T00:02:00",
            mgDl=95,
            record_type=GlucoseRecordType.historic,
        ),
        GlucoseRecord(
            timestamp="2021-01-01T20:00:00",
            mgDl=195,
            record_type=GlucoseRecordType.historic,
        ),
    ]
    result = _calculate_hba1c(glucose_records)
    assert result is not None
    assert abs(result["hba1c"] - 5.5226) < 0.00001
    assert result["cv"] > 0
