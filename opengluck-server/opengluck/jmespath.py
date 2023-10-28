from typing import List

import jmespath


def do_record_match_filter(record: dict, filter: str) -> bool:
    """Check if the given record matches the given filter."""
    if not filter:
        return True
    return bool(jmespath.search(filter, record))


def filter_records(records: List[dict], filter: str) -> List[dict]:
    """Filter the given records by the given filter."""
    return [record for record in records if do_record_match_filter(record, filter)]
