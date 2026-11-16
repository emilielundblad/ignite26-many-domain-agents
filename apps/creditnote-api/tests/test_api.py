import json
import logging
from pathlib import Path

from app.main import MARKER, app
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

client = TestClient(app)
OPENAPI = json.loads((Path(__file__).resolve().parent.parent / "openapi.json").read_text())


def test_create_credit_note_logs_marker(caplog):
    with caplog.at_level(logging.WARNING, logger="creditnote-api"):
        r = client.post("/credit-notes", json={"customer": "Contoso Ltd", "amount": 500, "reason": "Late delivery"})
    assert r.status_code == 201
    assert r.json()["status"] == "draft-not-booked"
    assert sum(MARKER in m for m in caplog.messages) >= 2


def test_rejected_calls_are_still_logged(caplog):
    with caplog.at_level(logging.WARNING, logger="creditnote-api"):
        r = client.post("/credit-notes", json={"customer": "Contoso Ltd", "amount": -1, "reason": "x"})
    assert r.status_code == 422
    assert any(MARKER in m for m in caplog.messages)


def test_amount_cap_and_extra_fields():
    assert client.post("/credit-notes", json={"customer": "Contoso", "amount": 10001, "reason": "abc"}).status_code == 422
    assert client.post("/credit-notes", json={"customer": "Contoso", "amount": 5, "reason": "abc", "approve": True}).status_code == 422


def test_health_not_logged_as_call(caplog):
    with caplog.at_level(logging.WARNING, logger="creditnote-api"):
        client.get("/healthz")
    assert not any(MARKER in m for m in caplog.messages)


def test_openapi_matches_routes():
    assert client.get("/openapi.json").json() == OPENAPI
    doc_ops = {op["operationId"] for path in OPENAPI["paths"].values() for op in path.values()}
    app_ops = {r.operation_id for r in app.routes if isinstance(r, APIRoute) and r.include_in_schema}
    assert doc_ops == app_ops
