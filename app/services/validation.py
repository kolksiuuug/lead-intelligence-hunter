from flask import abort
def validate_lead(data):
    if not isinstance(data, dict):
        abort(400)
    required_fields = ["source","source_id","url","text"]
    for field in required_fields: 
        value = data.get(field)
        if not isinstance(value, str) or not value.strip(): abort(400)
    optional_fields=["author","score","group","title"]
    for field in optional_fields:
        value = data.get(field)
        if field not in data or value is None: data[field]=None
    if not data["score"] is None and not isinstance(data["score"], (int, float)):
        abort(400)
    if data["score"] is not None and not 0 <= data["score"] <= 1: abort(400)
    strings = ["url", "text", "author", "group", "title"]
    for string in strings:
        if data[string] is not None and (not isinstance(data[string] , str) or isinstance(data["score"], bool)): abort(400)
    return True, None