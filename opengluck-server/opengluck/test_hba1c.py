from typing import cast

from opengluck.glucose import (GlucoseRecord, GlucoseRecordType,
                               find_glucose_records)

from .hba1c import _calculate_hba1c


def test_calculate_hba1c():
    assert _calculate_hba1c([]) is None

    glucose_records = [
        GlucoseRecord(
            timestamp="2021-01-01T00:00:00",
            mgDl=100,
            record_type=GlucoseRecordType.historic,
        ),
    ]
    assert (
        abs(cast(float, _calculate_hba1c(glucose_records)) - 5.111498257839721)
        < 0.00001
    )

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
    assert (
        abs(cast(float, _calculate_hba1c(glucose_records)) - 5.111498257839721)
        < 0.00001
    )

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
    assert cast(float, _calculate_hba1c(glucose_records)) > 5.111498257839721

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
    assert cast(float, _calculate_hba1c(glucose_records)) < 5.111498257839721

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
    assert (
        abs(cast(float, _calculate_hba1c(glucose_records)) - 4.850174216027875)
        < 0.00001
    )

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
    assert (
        abs(cast(float, _calculate_hba1c(glucose_records)) - 5.743031358885017)
        < 0.00001
    )
