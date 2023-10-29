"""OpenGlück configuration."""
import os

import pytz

"""The user timezone info."""
tz = pytz.timezone(os.environ.get("TZ", "UTC"))

"""The low threshold for glucose records."""
_merge_record_low_threshold_str = os.environ.get("MERGE_RECORD_LOW_THRESHOLD", "")
merge_record_low_threshold = (
    int(_merge_record_low_threshold_str) if _merge_record_low_threshold_str else 70
)

"""The high threshold for glucose records."""
_merge_record_high_threshold_str = os.environ.get("MERGE_RECORD_HIGH_THRESHOLD", "")
merge_record_high_threshold = (
    int(_merge_record_high_threshold_str) if _merge_record_high_threshold_str else 170
)
