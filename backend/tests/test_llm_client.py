from app.services.llm_client import _build_payload, _json_schema_format


def test_json_schema_format_estricto():
    schema = {"type": "object", "properties": {}, "additionalProperties": False}
    fmt = _json_schema_format(schema, "intent")
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["name"] == "intent"
    assert fmt["json_schema"]["strict"] is True
    assert fmt["json_schema"]["schema"] is schema


def test_build_payload_sin_formato():
    messages = [{"role": "user", "content": "hola"}]
    payload = _build_payload(messages)
    assert payload["messages"] == messages
    assert "response_format" not in payload


def test_build_payload_con_formato():
    payload = _build_payload([{"role": "user", "content": "x"}], _json_schema_format({}, "x"))
    assert payload["response_format"]["type"] == "json_schema"
