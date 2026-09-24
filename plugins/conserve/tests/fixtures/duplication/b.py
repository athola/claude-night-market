"""Planted duplicate, half two. Do not deduplicate; the detector must find it."""


def normalize_record(record: dict) -> dict:
    cleaned = {}
    for key, raw in record.items():
        if raw is None:
            continue
        cleaned[key.lower()] = raw.strip() if isinstance(raw, str) else raw
    if not cleaned:
        return {}
    return cleaned
