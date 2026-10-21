from flask import abort


def validate_lead(data):
    if not isinstance(data, dict):
        abort(400)

    required_fields = ["source", "source_id", "url", "text"]
    for field in required_fields:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            abort(400)

    optional_fields = ["author", "score", "group", "title"]
    for field in optional_fields:
        if field not in data or data[field] is None:
            data[field] = None

    if data["score"] is not None:
        if isinstance(data["score"], bool) or not isinstance(data["score"], (int, float)):
            abort(400)
        if not 0 <= data["score"] <= 1:
            abort(400)

    strings = ["author", "group", "title"]
    for field in strings:
        if data[field] is not None and not isinstance(data[field], str):
            abort(400)

    return True, None